import base64
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from flexagx.compute import (source_phase, observe, make_lut, decode, encode, render_pixels, png_decode, png_encode,
                             INSET,OUTSET,white_balance)
from flexagx.contracts import Settings
from flexagx.controller import SessionStore
from services.gateway import app as gateway_app
from services.observer import app as observer_app
from services.controller import app as controller_app
from services.tone import app as tone_app
from services.renderer import app as renderer_app


def fixture_png(width=12,height=10):
    yy,xx=np.indices((height,width))
    pix=np.zeros((height,width,4),dtype=np.uint8)
    pix[...,0]=(xx*19)%256
    pix[...,1]=(yy*29)%256
    pix[...,2]=((xx+yy)*11)%256
    pix[...,3]=255
    buf=io.BytesIO(); Image.fromarray(pix,'RGBA').save(buf,'PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


def test_reference_matrices_are_inverses():
    np.testing.assert_allclose(OUTSET@INSET,np.eye(3),atol=2e-12,rtol=0)


def test_transfer_functions_roundtrip_in_sdr():
    values=np.linspace(0,1,1001)
    for encoding in (0,1):
        np.testing.assert_allclose(encode(decode(values,encoding),encoding),values,atol=1e-12)


def test_phase_is_repeatable():
    assert source_phase(100)==source_phase(100)
    assert set(source_phase(0)).issubset({0,1})


def test_observer_checkerboard_aliasing():
    yy,xx=np.indices((32,32))
    image=np.repeat(((xx+yy)%2)[...,None],3,axis=-1).astype(float)
    obs=[observe(image,k,Settings()) for k in range(24)]
    assert all(o.sample_count==256 for o in obs)
    assert {o.white_count for o in obs}=={0,256}


def test_tone_validation():
    tone=make_lut(1.0,.5,50)
    assert tone.validation_passed
    assert len(tone.lut)==1024
    assert abs(tone.lut[0])<1e-12
    assert abs(tone.lut[-1]-1)<1e-12


def test_controller_isolates_sessions():
    store=SessionStore()
    img=np.ones((32,32,3),dtype=float)*.5
    obs=observe(img,1,Settings())
    result=store.step('a',obs,Settings(),16.7)
    assert result.initialized
    assert store.get('b')['kind']=='NOT_FOUND'
    assert store.get('a')['frames']==1
    assert store.reset('a')
    assert store.get('a')['kind']=='NOT_FOUND'


def test_renderer_exact_bypass_pixels():
    rgba=np.ones((3,4,4),dtype=float)*.6
    rgba[...,3]=.7
    s=Settings(OverallStrength=0)
    np.testing.assert_array_equal(render_pixels(rgba,s,[0.0]*1024),rgba)


def test_renderer_nontrivial_frame_and_alpha():
    h,w=8,8
    rgba=np.zeros((h,w,4),dtype=float)
    rgba[...,:3]=.2
    rgba[...,3]=.8
    s=Settings(LocalDetail=0,Dithering=False)
    out=render_pixels(rgba,s,make_lut(1,.5,50).lut)
    assert out.shape==rgba.shape and np.isfinite(out).all()
    np.testing.assert_allclose(out[...,3],.8)
    assert np.any(np.abs(out[...,:3]-rgba[...,:3])>1e-4)


def test_gateway_full_frame_and_bypass():
    cl=TestClient(gateway_app)
    png=fixture_png()
    params={'image_png_base64':png,'session_id':'test-e2e', 'frame_index':0,'dt_ms':16.7,
            'settings':{'LocalDetail':0,'Dithering':False}}
    result=cl.post('/v1/frame',json=params)
    assert result.status_code==200,result.text
    d=result.json()
    assert d['mode']=='processed'
    assert d['control'] is not None
    assert d['tone_validation']['validation_passed']
    assert png_decode(d['image_png_base64']).shape==(10,12,4)
    assert cl.get('/v1/sessions/test-e2e').json()['frames']==1
    params['settings']={'OverallStrength':0}; params['frame_index']=1
    bypass=cl.post('/v1/frame',json=params)
    assert bypass.status_code==200,bypass.text
    assert bypass.json()['image_png_base64']==png
    assert cl.get('/v1/sessions/test-e2e').json()['frames']==1
    assert cl.delete('/v1/sessions/test-e2e').json()['reset']


def test_each_microserver_endpoint():
    img=fixture_png(8,8)
    o=TestClient(observer_app).post('/v1/observe',json={'image_png_base64':img,'frame_index':2})
    assert o.status_code==200,o.text
    c=TestClient(controller_app).post('/v1/control/step',json={
        'session_id':'micro-e2e','dt_ms':16.7,'observation':o.json()})
    assert c.status_code==200,c.text
    tv=TestClient(tone_app).post('/v1/tone/build',json={
        'gain':c.json()['gain'],'knee':c.json()['knee'],'shadow_preservation':50})
    assert tv.status_code==200,tv.text
    output=TestClient(renderer_app).post('/v1/render',json={
        'image_png_base64':img,'gain_ev':c.json()['gain_ev'],
        'settings':{'LocalDetail':0,'Dithering':False},'lut':tv.json()['lut']})
    assert output.status_code==200,output.text
    assert png_decode(output.json()['image_png_base64']).shape==(8,8,4)
