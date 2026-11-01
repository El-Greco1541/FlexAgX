"""Seeded API fuzz, sentinel poisoning, transaction and response-contract probes.

Input intentionally contains JSON null/nonfinite tokens; evidence must never contain them.
All loops have explicit ceilings and all failures are recorded without aborting the campaign.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import random
import time
from fastapi.testclient import TestClient
from services.gateway import app as gateway
from services.observer import app as observer
from services.controller import app as controller
from services.tone import app as tone
from services.renderer import app as renderer
from flexagx.controller import SessionStore
from flexagx.compute import observe
from flexagx.contracts import Settings, Observation
from .phase import Audit, b64_png, pattern
from .run_sentinel_harness import valid_json
import numpy as np

APPS={'gateway':(gateway,'/v1/frame'), 'observer':(observer,'/v1/observe'),
      'controller':(controller,'/v1/control/prepare'), 'tone':(tone,'/v1/tone/build'),
      'renderer':(renderer,'/v1/render')}


def get_seed(seed):
    raw=b64_png(pattern(seed,3,3,'checker'))
    obs={'histogram':[0]*63+[64],'valid_count':64,'white_count':0,'sample_count':64,
         'e50':0.0,'e90':0.0,'phase_x':0,'phase_y':0}
    tone_lut=[i/1023 for i in range(1024)]
    return {'gateway':{'image_png_base64':raw,'frame_index':1,'session_id':'fuzz','settings':{'OverallStrength':0}},
            'observer':{'image_png_base64':raw,'frame_index':1},
            'controller':{'session_id':'fuzz-control','dt_ms':16.67,'observation':obs},
            'tone':{'gain':1.0,'knee':0.5,'shadow_preservation':50},
            'renderer':{'image_png_base64':raw,'gain_ev':0.0,'lut':tone_lut}}


def fuzz(a:Audit):
    clients={name:TestClient(app,raise_server_exceptions=False) for name,(app,path) in APPS.items()}
    paths={name:path for name,(app,path) in APPS.items()}
    rng=random.Random(a.seed ^ 0x5A5AF00D)
    originals=get_seed(a.seed)
    random_values=[None,True,False,0,1,-1,1e100,-1e100,{'x':None},[],[None],
                   'x'*128,'\u2603','../',{'__proto__':{'polluted':True}},[[]],{'nested':{'c':[0,1,2]}}]
    for i in range(400):
        service=rng.choice(list(APPS))
        source=originals[service].copy()
        field=rng.choice(list(source)+['settings','unknown-field'])
        source[field]=rng.choice(random_values)
        def task(service=service,body=source):
            r=clients[service].post(paths[service],json=body)
            assert 200<=r.status_code<500, (service,r.status_code,r.text[:120])
            try: result=r.json()
            except ValueError: raise AssertionError('response was not JSON')
            valid_json(result)
            if r.status_code>=400: assert isinstance(result.get('error'),dict),result
            return {'http':r.status_code,'service':service}
        a.check(f'api_structural_fuzz_{i:03}',task)

    malformed=['{}','null','[]','true','0','"str"','{"x":NaN}',
               '{"x":Infinity}','{"x":-Infinity}','{'+'"x":['*15+'0'+']'*15+'}',
               '{"__proto__":{"polluted":true}}','{"image_png_base64":"abc"',
               '{"nested":'+ '{"x":'*16+'0'+'}'*16+'}']
    for service in APPS:
        for j,payload in enumerate(malformed):
            def task(service=service,payload=payload):
                response=clients[service].post(paths[service],content=payload,
                                                headers={'content-type':'application/json'})
                assert response.status_code<500, (service,response.status_code,response.text[:120])
                valid_json(response.json())
                return response.status_code
            a.check(f'raw_json_{service}_{j:02}',task)

    for service in APPS:
        for j in range(20):
            baseline=originals[service].copy()
            field=rng.choice(list(baseline))
            raw=json.dumps(baseline,separators=(',',':'),allow_nan=False)
            # Repeated declaration of the same key, or an explicit non-finite scalar.
            if j%2==0:
                raw=raw[:-1]+',"'+field+'":null}'
            else:
                raw=raw[:-1]+',"'+field+'":NaN}'
            def task(service=service,raw=raw):
                r=clients[service].post(paths[service],content=raw,
                                        headers={'content-type':'application/json'})
                assert 200<=r.status_code<500, (service,r.status_code,r.text[:100])
                valid_json(r.json())
                return r.status_code
            a.check(f'duplicate_key_or_nonfinite_{service}_{j:02}',task)

    def control_transactions():
        settings=Settings()
        pixels=np.ones((16,16,3),dtype=float)
        ob=observe(pixels,0,settings)
        store=SessionStore(max_sessions=2)
        first=store.prepare('s1',ob,settings,16.67)
        try:
            store.prepare('s1',ob,settings,16.67)
        except ValueError: pass
        else: raise AssertionError('same-session concurrent preparation allowed')
        assert store.get('s1')['kind']=='NOT_FOUND'
        aborted=store.abort(first.token)
        assert aborted.state=='ABORTED'
        assert store.get('s1')['kind']=='NOT_FOUND'
        second=store.prepare('s1',ob,settings,16.67)
        assert store.commit(second.token).committed
        assert not store.commit(second.token).committed
        assert store.get('s1')['frames']==1
        third=store.prepare('s1',ob,settings,16.67)
        assert store.reset('s1')
        assert not store.commit(third.token).committed
        assert store.get('s1')['kind']=='NOT_FOUND'
        return {'transaction_checks':10,'sentinel':'NOT_FOUND'}
    a.check('prepare_commit_abort_reset_invariants', control_transactions)

    def bounded_pending():
        settings=Settings(); ob=observe(np.ones((16,16,3)),0,settings)
        store=SessionStore(max_sessions=128)
        preps=[]
        for j in range(128): preps.append(store.prepare('pending_'+str(j),ob,settings,16.67).token)
        try:store.prepare('pending_overflow',ob,settings,16.67)
        except ValueError: pass
        else:raise AssertionError('pending limit bypass')
        for token in preps: store.abort(token)
        assert len(store._pending)==0
        return {'tokens':128,'pending_after_cleanup':0}
    a.check('pending_capacity_ceiling',bounded_pending)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=20261101)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    if not (0<=args.seed<=2**63-1):p.error('seed invalid')
    a=Audit('adversarial',args.seed)
    fuzz(a)
    data=a.result()
    valid_json(data)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'phase':'adversarial','checks':data['checks'],'passed':data['passed'],'failed':data['failed']}))
    return 1 if data['failed'] else 0

if __name__=='__main__':raise SystemExit(main())
