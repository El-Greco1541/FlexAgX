"""Sentinel / bounded-resource / fallbacks assurance tests: staged CPU services only."""
import base64
import io
import json
import math
import time

import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from pydantic import ValidationError

from flexagx.contracts import (Observation, Settings, ToneResult, RenderRequest, Sentinel,
                               FrameRequest)
from flexagx.controller import SessionStore
from flexagx.compute import observe, make_lut, png_encode
import services.gateway as gateway
from services.controller import app as controller_app
from services.tone import app as tone_app
from services.renderer import app as renderer_app
from services.observer import app as observer_app


def image_b64():
    arr=np.zeros((8, 8, 4),dtype=np.uint8)
    arr[...,:3]=100;arr[...,3]=255
    buf=io.BytesIO();Image.fromarray(arr,'RGBA').save(buf,format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


def assert_sentinels_only(value):
    assert value is not None, 'null is forbidden: expected typed sentinel'
    if isinstance(value, dict):
        for k, v in value.items(): assert_sentinels_only(v)
    if isinstance(value, list):
        for v in value: assert_sentinels_only(v)
    if isinstance(value,float): assert math.isfinite(value)


@pytest.mark.parametrize('app', [gateway.app, observer_app, controller_app, tone_app, renderer_app])
def test_health_and_openapi_contain_no_nulls(app):
    c=TestClient(app,raise_server_exceptions=False)
    for path in ('/health','/openapi.json'):
        r=c.get(path)
        assert r.status_code==200, r.text[:300]
        assert_sentinels_only(r.json())


def test_bypass_writes_sentinels_instead_of_null():
    c=TestClient(gateway.app,raise_server_exceptions=False)
    data={'image_png_base64':image_b64(),'frame_index':0,'session_id':'sentinel-bypass','settings':{'OverallStrength':0}}
    r=c.post('/v1/frame',json=data)
    assert r.status_code==200,r.text[:300]
    body=r.json();assert_sentinels_only(body)
    for field in ['observation','control','tone_validation']:
        assert body[field]['kind']=='NOT_APPLICABLE'
        assert body[field]['fallback']=='IDENTITY'


@pytest.mark.parametrize('app,path,payload',[ 
    (gateway.app,'/v1/frame',{'image_png_base64':'invalid','frame_index':0,'settings':{'OverallStrength':None}}),
    (gateway.app,'/v1/frame',{'image_png_base64':None,'frame_index':0}),
    (tone_app,'/v1/tone/build',{'gain':None,'knee':.5,'shadow_preservation':50}),
    (controller_app,'/v1/control/prepare',{'session_id':None}),
    (renderer_app,'/v1/render',{'image_png_base64':None}),
])
def test_incoming_null_rejected_with_sentinal(app,path,payload):
    r=TestClient(app,raise_server_exceptions=False).post(path,json=payload)
    assert r.status_code==422, r.text[:300]
    body=r.json();assert_sentinels_only(body)
    assert body['error']['kind']=='INVALID'
    assert body['error']['fallback']=='REJECT'


@pytest.mark.parametrize('token',['NaN','Infinity','-Infinity','1e308'])
def test_tone_out_of_domain_fails_closed(token):
    payload='{"gain":'+token+',"knee":0.5,"shadow_preservation":50}'
    r=TestClient(tone_app,raise_server_exceptions=False).post('/v1/tone/build',content=payload,headers={'content-type':'application/json'})
    assert r.status_code==422,r.text[:300]
    assert_sentinels_only(r.json())


def test_lut_nonfinite_and_outside_limits_rejected():
    raw=image_b64()
    for value in [float('nan'),float('inf'),float('-inf'),-0.1,1.5]:
        lut=[i/1023 for i in range(1024)];lut[512]=value
        with pytest.raises(ValidationError):
            RenderRequest(image_png_base64=raw,gain_ev=0,lut=lut)


def test_observer_population_is_consistent_and_bounded():
    data={'histogram':[0]*63+[64], 'valid_count':64,'white_count':0,'sample_count':64,
          'e50':0,'e90':0,'phase_x':0,'phase_y':0}
    assert Observation(**data).valid_count==64
    for override in ({'valid_count':0},{'white_count':65},{'sample_count':63},
                     {'e50':1e308},{'phase_x':2}):
        with pytest.raises(ValidationError): Observation(**{**data,**override})


def test_transaction_commit_abort_and_expiry():
    store=SessionStore()
    rgba=np.zeros((32,32,3));rgba[...]=.45
    obs=observe(rgba,0,Settings())
    p=store.prepare('a',obs,Settings(),16.6)
    assert store.get('a')['kind']=='NOT_FOUND'
    assert store.abort(p.token).state=='ABORTED'
    assert store.get('a')['kind']=='NOT_FOUND'
    p=store.prepare('a',obs,Settings(),16.6)
    assert store.commit(p.token).committed
    assert store.get('a')['frames']==1
    assert store.commit(p.token).committed is False
    p=store.prepare('b',obs,Settings(),16.6)
    token=p.token;owner,base,candidate,expiry=store._pending[token]
    store._pending[token]=(owner,base,candidate,time.monotonic()-1.0)
    assert store.commit(token).state=='EXPIRED'
    assert store.get('b')['kind']=='NOT_FOUND'


def test_transaction_limits_and_conflicts():
    store=SessionStore(max_sessions=1)
    rgba=np.ones((32,32,3))*.4
    obs=observe(rgba,0,Settings())
    p=store.prepare('a',obs,Settings(),16.6)
    with pytest.raises(ValueError,match='pending'):
        store.prepare('a',obs,Settings(),16.6)
    assert store.commit(p.token).committed
    with pytest.raises(ValueError,match='capacity'):
        store.prepare('b',obs,Settings(),16.6)


def test_gateway_render_failure_rolls_back_local_state(monkeypatch):
    c=TestClient(gateway.app,raise_server_exceptions=False)
    def fail(*args,**kwargs): raise ValueError('forced pre-commit failure')
    monkeypatch.setattr(gateway,'render_pixels',fail)
    request={'image_png_base64':image_b64(),'frame_index':0,'session_id':'rollback-test-0'}
    r=c.post('/v1/frame',json=request)
    assert r.status_code==422,r.text[:300]
    assert_sentinels_only(r.json())
    assert c.get('/v1/sessions/rollback-test-0').status_code==404


def test_local_processed_response_commits_once():
    c=TestClient(gateway.app,raise_server_exceptions=False)
    request={'image_png_base64':image_b64(),'frame_index':0,'session_id':'one-commit-test-1'}
    r=c.post('/v1/frame',json=request)
    assert r.status_code==200,r.text[:300]
    assert_sentinels_only(r.json())
    assert c.get('/v1/sessions/one-commit-test-1').json()['frames']==1
    assert c.delete('/v1/sessions/one-commit-test-1').status_code==200


def test_missing_session_response_sentinel():
    c=TestClient(gateway.app,raise_server_exceptions=False)
    r=c.get('/v1/sessions/not-real')
    assert r.status_code==404
    assert r.json()['error']['kind']=='NOT_FOUND'
    assert_sentinels_only(r.json())


def test_bounded_request_header():
    c=TestClient(gateway.app,raise_server_exceptions=False)
    r=c.post('/v1/frame',content=b'{}',headers={'content-type':'application/json','content-length':'21000001'})
    assert r.status_code==413,r.text[:300]
    assert r.json()['error']['kind']=='LIMIT_EXCEEDED'
    assert_sentinels_only(r.json())


def test_reject_unrecognized_settings_and_undefined_state():
    with pytest.raises(ValidationError): Settings(UnrecognizedSetting=True)
    with pytest.raises(ValidationError): FrameRequest(image_png_base64=image_b64(),frame_index=0,extra=3)
    assert Sentinel(kind='UNINITIALIZED',reason='not yet sampled').model_dump()['kind']=='UNINITIALIZED'


def test_png_output_rejects_nonfinite():
    pixels=np.ones((2,2,4));pixels[0,0,0]=float('nan')
    with pytest.raises(ValueError,match='non-finite'): png_encode(pixels)
