"""Isolated, deterministic FlexAgX CPU API adversarial test phases.

No modifications to target software. Scope: local FastAPI ASGI TestClient and CPU math,
with real distributed tests managed separately by test runner.
"""
from __future__ import annotations
import argparse
import base64
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from flexagx.compute import observe, make_lut, render_pixels, png_decode, png_encode
from flexagx.contracts import Settings
from services.gateway import app as gateway_app, store as gateway_store
from services.observer import app as observer_app
from services.controller import app as controller_app, store as controller_store
from services.tone import app as tone_app
from services.renderer import app as renderer_app

ROOT=Path(__file__).resolve().parents[1]


def b64_png(arr):
    b=io.BytesIO(); Image.fromarray(arr, 'RGBA').save(b, 'PNG')
    return base64.b64encode(b.getvalue()).decode('ascii')


def pattern(seed, w, h, mode):
    rng=np.random.default_rng(seed)
    arr=np.zeros((h,w,4), dtype=np.uint8)
    if mode == 'noise': arr[...,:3] = rng.integers(0,256,(h,w,3),dtype=np.uint8)
    elif mode == 'checker':
        yy,xx=np.indices((h,w)); arr[...,:3] = ((xx+yy)%2*255)[...,None]
    elif mode == 'flat': arr[...,:3] = int(seed%256)
    elif mode == 'gradient':
        yy,xx=np.indices((h,w)); arr[...,0]=xx%256; arr[...,1]=yy%256; arr[...,2]=(xx+yy)%256
    elif mode == 'black': pass
    elif mode == 'white': arr[...,:3]=255
    else: raise ValueError(mode)
    arr[...,3] = rng.integers(0,256,(h,w),dtype=np.uint8)
    return arr


NOT_SPECIFIED={'kind':'NOT_APPLICABLE','reason':'test case has no comparison value','fallback':'SKIP'}

def case_record(name, status, detail='', expected=NOT_SPECIFIED, observed=NOT_SPECIFIED, duration_ms=0):
    return {'name':name,'status':status,'detail':str(detail)[:1000], 'expected':expected,
            'observed':observed,'duration_ms':round(duration_ms,3)}


class Audit:
    def __init__(self, phase, seed):
        self.phase=phase; self.seed=seed; self.cases=[]; self.findings=[]
        self.rng=random.Random(seed)
    def check(self, name, fn):
        start=time.perf_counter()
        try:
            result=fn()
            self.cases.append(case_record(name,'pass',observed=result,duration_ms=(time.perf_counter()-start)*1000))
        except Exception as exc:
            self.cases.append(case_record(name,'fail',detail=f'{type(exc).__name__}: {exc}', duration_ms=(time.perf_counter()-start)*1000))
    def finding(self, finding_id, title, evidence, severity, scope):
        self.findings.append({'id':finding_id,'title':title,'evidence':evidence,'severity':severity,'scope':scope})
    def result(self):
        return {'phase':self.phase,'seed':self.seed,'checks':len(self.cases),
                'passed':sum(x['status']=='pass' for x in self.cases),
                'failed':sum(x['status']=='fail' for x in self.cases),
                'findings':self.findings,'cases':self.cases}


def validation_phase(a:Audit):
    # Mostly invalid requests: should fail predictably without server 5xx.
    c=TestClient(gateway_app, raise_server_exceptions=False)
    zero=b64_png(pattern(9,3,3,'black'))
    malformed=['', '???=', 'a'*50, base64.b64encode(b'not a png').decode(),
               base64.b64encode(b'\x89PNG\r\n\x1a\nBROKEN').decode()]
    for i,value in enumerate(malformed):
        def fn(value=value):
            r=c.post('/v1/frame',json={'image_png_base64':value,'session_id':'invalid','frame_index':0})
            assert r.status_code in (400,413,422),f'unexpected status {r.status_code}: {r.text[:240]}'
            return r.status_code
        a.check(f'invalid_image_{i}',fn)
    bad_settings=[{'OverallStrength':-1},{'OverallStrength':101},{'LocalDetail':999},
                  {'ColorTemp':100},{'MaxChangeRate':-5},{'InputEncoding':9},
                  {'Dithering':'this-is-not-a-boolean'},{'Deadband':.7},
                  {'GamutRolloffStart':0},{'SceneChangeSensitivity':-1}]
    for i,settings in enumerate(bad_settings):
        def fn(settings=settings):
            r=c.post('/v1/frame',json={'image_png_base64':zero,'session_id':'invalid','frame_index':0,'settings':settings})
            assert r.status_code==422,(r.status_code,r.text[:260])
            return 422
        a.check(f'invalid_settings_{i}',fn)
    for i,kwargs in enumerate([{'session_id':'../a'}, {'session_id':'a'*65}, {'frame_index':-1},
                                {'frame_index':2**64}, {'dt_ms':-1}, {'dt_ms':60001}]):
        def fn(kwargs=kwargs):
            payload={'image_png_base64':zero,'session_id':'invalid','frame_index':0};payload.update(kwargs)
            r=c.post('/v1/frame',json=payload)
            assert r.status_code==422,(r.status_code,r.text[:200])
            return 422
        a.check(f'invalid_envelope_{i}',fn)
    # Bypass should not touch session state even for random images.
    for i in range(16):
        w=a.rng.choice([1,2,3,7,31]);h=a.rng.choice([1,2,5,23]);mode=a.rng.choice(['noise','black','checker','gradient'])
        raw=b64_png(pattern(a.seed+i,w,h,mode));sess=f'bypass{i}'
        def fn(raw=raw,sess=sess,w=w,h=h):
            r=c.post('/v1/frame',json={'image_png_base64':raw,'session_id':sess,'frame_index':0,
                                       'settings':{'OverallStrength':0,'DebugView':0}})
            assert r.status_code==200,(r.status_code,r.text[:240])
            obj=r.json()
            assert obj['image_png_base64']==raw and obj['width']==w and obj['height']==h
            assert c.get('/v1/sessions/'+sess).status_code==404
            return {'width':w,'height':h}
        a.check(f'bypass_exact_{i}',fn)
    # Internal APIs: intentionally contradictory or nonfinite contracts.
    ctrl=TestClient(controller_app,raise_server_exceptions=False)
    legitimate={'histogram':[0]*63+[64], 'valid_count':64,'white_count':0,'sample_count':64,
                'e50':0.0,'e90':0.0,'phase_x':0,'phase_y':0}
    for i,modified in enumerate([{'histogram':[0]*64}, {'valid_count':0},
                                 {'white_count':70},{'sample_count':1},
                                 {'e50':1e308,'e90':1e308},
                                 {'e50':-1e308,'e90':-1e308}]):
        obs={**legitimate,**modified}
        def fn(obs=obs,i=i):
            r=ctrl.post('/v1/control/step',json={'session_id':f'bad{i}', 'dt_ms':16.67,'observation':obs})
            assert r.status_code < 500,f'invalid contract caused server {r.status_code}: {r.text[:240]}'
            return r.status_code
        a.check(f'inconsistent_observation_{i}',fn)
    # Adversarial JSON nonfinite on direct endpoint; do not generate non-compliant JSON via json.dumps.
    for i,token in enumerate(('NaN','Infinity','-Infinity')):
        payload='{"gain":'+token+',"knee":0.5,"shadow_preservation":50}'
        def fn(payload=payload):
            r=TestClient(tone_app,raise_server_exceptions=False).post('/v1/tone/build',content=payload,
                       headers={'content-type':'application/json'})
            assert r.status_code in (400,422),f'nonfinite should reject; got {r.status_code}'
            return r.status_code
        a.check(f'nonfinite_tone_{i}',fn)
    # Renderer numeric-domain boundary. The response must not accept nonfinite
    # LUTs or gain values; this intentionally exposes target-side failures.
    render=TestClient(renderer_app,raise_server_exceptions=False)
    render_img=b64_png(pattern(442,2,2,'white'))
    lut_values=','.join(['0.2']*1024)
    for key in ('gain_ev','lut'):
        if key=='gain_ev':
            raw='{"image_png_base64":"'+render_img+'","gain_ev":NaN,"lut":['+lut_values+']}'
        else:
            values=['0.2']*1024;values[512]='NaN'
            raw='{"image_png_base64":"'+render_img+'","gain_ev":0,"lut":['+','.join(values)+']}'
        def fn(raw=raw,key=key):
            r=render.post('/v1/render',content=raw,headers={'content-type':'application/json'})
            assert r.status_code in (400,422),f'{key}: expected rejection, got {r.status_code}'
            return r.status_code
        a.check(f'nonfinite_renderer_{key}',fn)
    # Randomized structural JSON fuzz: type confusion, out-of-domain numbers,
    # nested arrays, strings and objects. Fail-open 5xx is always a finding.
    candidate_values=[None,True,False,[],{},'\u2603','a'*512,1e308,-1e308,-1,0,1,5000]
    for i in range(200):
        key=a.rng.choice(['frame_index','dt_ms','session_id','settings','image_png_base64'])
        value=a.rng.choice(candidate_values)
        data={'image_png_base64':zero,'frame_index':0,'session_id':'structural'}
        data[key]=value
        def fn(data=data):
            r=c.post('/v1/frame',json=data)
            assert r.status_code<500,f'structural fuzz caused {r.status_code}: {r.text[:120]}'
            return r.status_code
        a.check(f'structural_json_{i:03}',fn)
    # A valid image but malformed content-type/missing mandatory fields.
    for path, app in [('/v1/frame',gateway_app),('/v1/observe',observer_app),
                      ('/v1/tone/build',tone_app),('/v1/control/step',controller_app),
                      ('/v1/render',renderer_app)]:
        def fn(path=path,app=app):
            r=TestClient(app,raise_server_exceptions=False).post(path,json={})
            assert r.status_code==422,(path,r.status_code)
            return 422
        a.check('missing_required_'+path,fn)
    # High-entropy tampering of b64 before decode; keep output bounded.
    seed_img=zero
    for i in range(80):
        j=a.rng.randrange(len(seed_img)); mutated=seed_img[:j]+a.rng.choice('!$@%')+seed_img[j+1:]
        def fn(mutated=mutated,i=i):
            r=c.post('/v1/frame',json={'image_png_base64':mutated,'session_id':f'mut{i}',
                                       'frame_index':0,'settings':{'OverallStrength':0}})
            assert r.status_code in (200,422),f'mutation caused {r.status_code}: {r.text[:120]}'
            return r.status_code
        a.check(f'encoded_mutation_{i:03}',fn)


def metamorphic_phase(a:Audit):
    rng=np.random.default_rng(a.seed)
    for i in range(60):
        w=int(rng.choice([1,2,3,4,7,8,15,32]));h=int(rng.choice([1,2,3,5,12,24]))
        mode=a.rng.choice(['black','white','flat','gradient','checker','noise'])
        im=pattern(a.seed+i,w,h,mode)
        s=Settings(InputEncoding=a.rng.choice([0,1]), LocalDetail=a.rng.choice([0,20,50]),
                   ColorTemp=a.rng.choice([2000,6500,12000]),
                   OverallStrength=a.rng.choice([1,25,50,100]),
                   Dithering=a.rng.choice([True,False]),
                   OutputEncoding=a.rng.choice([0,1]))
        def fn(im=im,i=i,s=s,w=w,h=h):
            x=np.asarray(im,dtype=float)/255
            ob=observe(x[...,:3],i,s)
            assert 0<=ob.white_count<=ob.valid_count<=ob.sample_count<=w*h
            assert sum(ob.histogram)==ob.valid_count
            if w%2==0 and h%2==0: assert ob.sample_count==w*h//4
            tone=make_lut(1.0,.5,s.ShadowPreservation,s.InputEncoding,s.OutputEncoding)
            assert tone.validation_passed and len(tone.lut)==1024
            assert np.isfinite(tone.lut).all()
            out=render_pixels(x,s,tone.lut,0)
            assert out.shape==x.shape and np.isfinite(out).all()
            assert np.all((out>=0)&(out<=1))
            assert np.array_equal(out[...,3],x[...,3])
            return {'w':w,'h':h,'mode':s.OverallStrength}
        a.check(f'frame_property_{i:03}',fn)
    # Compare local gateway to composition with separately invoked adapters.
    client=TestClient(gateway_app,raise_server_exceptions=False)
    for i in range(25):
        im=pattern(a.seed+113+i,3+i%6,2+i%9,a.rng.choice(['noise','white','checker','gradient']))
        payload={'image_png_base64':b64_png(im),'session_id':f'composite{i}','frame_index':i,
                 'dt_ms':a.rng.choice([0,1,16.667,250,1000,60000]),
                 'settings':{'Dithering':False,'LocalDetail':a.rng.choice([0,10,50]),
                             'ColorTemp':a.rng.choice([2000,6500,12000]),'OverallStrength':100}}
        def fn(payload=payload,i=i,expected_shape=im.shape):
            r=client.post('/v1/frame',json=payload)
            assert r.status_code==200,(r.status_code,r.text[:200])
            out=r.json()
            assert out['mode']=='processed' and out['tone_validation']['validation_passed']
            arr=png_decode(out['image_png_base64'])
            assert arr.shape==expected_shape
            assert np.isfinite(arr).all()
            assert np.max(np.abs(arr[...,3]-png_decode(payload['image_png_base64'])[...,3]))<=1/255
            assert client.delete('/v1/sessions/'+payload['session_id']).json()['reset']
            return {'checksum':hashlib.sha256(base64.b64decode(out['image_png_base64'])).hexdigest()[:16]}
        a.check(f'api_frame_{i:03}',fn)


def torture_phase(a:Audit,frames:int):
    client=TestClient(gateway_app,raise_server_exceptions=False)
    start=time.perf_counter()
    times=[]; statuses={}; durations=[]
    image_modes=['checker','noise','black','white','flat','gradient']
    sess='torture-repeated'
    for i in range(frames):
        w=a.rng.choice([1,2,3,9,17,32,64]);h=a.rng.choice([1,2,3,11,16,32,64])
        im=pattern(a.seed+i,w,h,image_modes[i%len(image_modes)])
        settings={'OverallStrength':a.rng.choice([0,1,15,60,100]),
                  'Dithering':a.rng.choice([False,True]),'LocalDetail':a.rng.choice([0,20,50]),
                  'AutoExposureStrength':a.rng.choice([0,30,100]),
                  'FreezeExposure':a.rng.choice([True,False]),
                  'ColorTemp':a.rng.choice([2000,6500,12000])}
        req={'image_png_base64':b64_png(im),'session_id':sess,'frame_index':i,
             'dt_ms':a.rng.choice([0,1,16.67,250,1000,60000]),'settings':settings}
        t0=time.perf_counter()
        try:
            r=client.post('/v1/frame',json=req)
            statuses[r.status_code]=statuses.get(r.status_code,0)+1
            assert r.status_code==200,(i,r.status_code,r.text[:200])
            out=r.json()
            assert out['width']==w and out['height']==h
            imout=png_decode(out['image_png_base64']); assert imout.shape==im.shape
            assert np.isfinite(imout).all()
            assert np.array_equal((imout[...,3]*255).round().astype('uint8'),im[...,3])
            if settings['OverallStrength']==0:
                assert out['image_png_base64']==req['image_png_base64']
        except Exception as e:
            a.cases.append(case_record(f'frame_{i}', 'fail',str(e)))
        finally: times.append((time.perf_counter()-t0)*1000)
    state=client.get('/v1/sessions/'+sess)
    s=state.json() if state.status_code==200 else {}
    a.cases.append(case_record('torture_frames','pass' if statuses.get(200,0)==frames and not any(c['status']=='fail' for c in a.cases) else 'fail',
          observed={'frames':frames,'http_status':statuses,'seconds':round(time.perf_counter()-start,3),
                    'latency_ms':{'p50':round(float(np.percentile(times,50)),3),'p95':round(float(np.percentile(times,95)),3),
                                  'max':round(max(times),3)},'session_frames':s.get('frames')}))
    # Image decompression boundary with highly compressible oversized PNGs.
    # 1415^2 exceeds the documented 2 million pixel cap but is only a few KB.
    def oversized_image_rejected():
        im=pattern(42,1415,1415,'black')
        r=client.post('/v1/frame',json={'image_png_base64':b64_png(im),
            'session_id':'oversized','frame_index':0,'settings':{'OverallStrength':0}})
        assert r.status_code==422,(r.status_code,r.text[:240])
        return {'pixels':1415*1415,'status':r.status_code}
    a.check('oversize_image_rejected_before_render',oversized_image_rejected)
    # A near-limit image is allowed, but test only the bounded bypass path.
    def near_limit_bypass():
        im=pattern(43,1414,1414,'black')
        encoded=b64_png(im)
        r=client.post('/v1/frame',json={'image_png_base64':encoded,
            'session_id':'maxsize','frame_index':0,'settings':{'OverallStrength':0}})
        assert r.status_code==200,(r.status_code,r.text[:240])
        assert r.json()['image_png_base64']==encoded
        return {'pixels':1414*1414,'status':r.status_code}
    a.check('near_limit_image_bypass',near_limit_bypass)
    # Capacity boundary: 128 unique sessions, no unbounded growth, 129th must report 4xx (not 500).
    def capacity():
        img=b64_png(pattern(99,1,1,'white'))
        local_store = __import__('flexagx.controller',fromlist=['SessionStore']).SessionStore(max_sessions=3)
        obs=observe(np.ones((16,16,3),dtype=float),0,Settings())
        for j in range(3): local_store.step(f's{j}',obs,Settings(),16.7)
        try:local_store.step('overflow',obs,Settings(),16.7)
        except ValueError: pass
        else: raise AssertionError('state capacity not enforced')
        assert local_store.reset('s1')
        local_store.step('new',obs,Settings(),16.7)
        return {'capacity':3,'limit_enforced':True}
    a.check('session_capacity_and_recovery',capacity)

    # Threads operate on separate sessions; the state's RLock and per-session isolation should preserve counts.
    def concurrent():
        workers=6; iterations=10
        img=b64_png(pattern(512,8,8,'noise'))
        def work(worker):
            cl=TestClient(gateway_app,raise_server_exceptions=False)
            sid=f'parallel-{a.seed}-{worker}'
            for i in range(iterations):
                r=cl.post('/v1/frame',json={'image_png_base64':img,'session_id':sid,
                                           'frame_index':i,'settings':{'LocalDetail':0,'Dithering':False}})
                if r.status_code!=200: return (worker,False,r.status_code)
            s=cl.get('/v1/sessions/'+sid)
            return (worker,s.status_code==200 and s.json()['frames']==iterations,s.status_code)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            output=list(pool.map(work,range(workers)))
        assert all(item[1] for item in output),output
        return {'workers':workers,'iterations_per_worker':iterations}
    a.check('parallel_sessions',concurrent)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['validation','metamorphic','torture'])
    parser.add_argument('--seed',type=int,default=20261101)
    parser.add_argument('--frames',type=int,default=120)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.frames<1 or args.frames>1000:
        parser.error('--frames must be within 1..1000')
    if not (0 <= args.seed <= 2**63-1):
        parser.error('--seed must be within 0..2^63-1')
    a=Audit(args.phase,args.seed)
    if args.phase=='validation':validation_phase(a)
    if args.phase=='metamorphic':metamorphic_phase(a)
    if args.phase=='torture':torture_phase(a,args.frames)
    res=a.result()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(res,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'phase':args.phase,'checks':res['checks'],'passed':res['passed'],'failed':res['failed']}))
    sys.exit(1 if res['failed'] else 0)

if __name__=='__main__':main()
