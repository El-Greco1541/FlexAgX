"""v0.5.0 transaction integrity: reproducible local, persistence, rollback, fuzz and concurrency."""
import base64
import io
import json
import math
import random
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from flexagx.controller import SessionStore
from flexagx.contracts import FrameRequest, Settings
from flexagx.compute import png_decode, observe
import services.gateway as gateway


def fixture_png(seed=7):
    rng=random.Random(seed)
    image=Image.new('RGBA',(8,8))
    image.putdata([(rng.randrange(256),rng.randrange(256),rng.randrange(256),255) for _ in range(64)])
    b=io.BytesIO();image.save(b,format='PNG')
    return base64.b64encode(b.getvalue()).decode('ascii')


def req(session='v05',index=0,seed=7,settings=None):
    return {'session_id':session,'frame_index':index,'image_png_base64':fixture_png(seed),
            'dt_ms':16.667,'settings':settings or {'LocalDetail':0,'Dithering':False}}


def no_null(x):
    assert x is not None
    if isinstance(x,dict):
        for v in x.values(): no_null(v)
    elif isinstance(x,list):
        for v in x:no_null(v)
    elif isinstance(x,float): assert math.isfinite(x)


def post(client,data,code=200):
    r=client.post('/v1/frame',json=data)
    assert r.status_code==code,r.text[:500]
    no_null(r.json())
    return r.json()


def test_replays_are_identical_no_advancement(monkeypatch,tmp_path):
    store=SessionStore(db_path=str(tmp_path/'db.sqlite'))
    monkeypatch.setattr(gateway,'store',store)
    with TestClient(gateway.app) as client:
        frame=req('one',9)
        first=post(client,frame)
        for _ in range(9): assert post(client,frame)==first
        assert store.get('one')['frames']==1
        assert post(client,{**frame,'dt_ms':20},409)['error']['fallback']=='REJECT'
        assert post(client,{**frame,'image_png_base64':fixture_png(8)},409)['error']['kind']=='INVALID'
        assert post(client,req('one',8),409)['error']['kind']=='INVALID'
        post(client,req('one',10))
        assert store.get('one')['frames']==2


def test_persistence_restart_and_lost_ack(monkeypatch,tmp_path):
    db=tmp_path/'state.sqlite'
    store=SessionStore(db_path=str(db))
    monkeypatch.setattr(gateway,'store',store)
    with TestClient(gateway.app) as client:
        data=req('restart',0)
        result=post(client,data)
        assert result['control']['gain']>0
    recovered=SessionStore(db_path=str(db))
    assert recovered.get('restart')['frames']==1
    monkeypatch.setattr(gateway,'store',recovered)
    with TestClient(gateway.app) as client:
        assert post(client,data)==result
        assert recovered.get('restart')['frames']==1
        post(client,req('restart',1))
    assert SessionStore(db_path=str(db)).get('restart')['frames']==2


def test_aborted_prepared_frame_not_committed_across_restart(tmp_path):
    db=tmp_path/'state.sqlite'
    store=SessionStore(db_path=str(db))
    arr=png_decode(fixture_png(1))
    obs=observe(arr[...,:3],1,Settings())
    store.prepare('crashed',obs,Settings(),16.6,frame_index=5,request_digest='f'*64)
    assert store.get('crashed')['kind']=='NOT_FOUND'
    store2=SessionStore(db_path=str(db))
    assert store2.receipt('crashed',5,'f'*64).status=='NEW'
    assert store2.get('crashed')['kind']=='NOT_FOUND'


def test_bypass_is_journaled_without_advancing_temporal_state(monkeypatch,tmp_path):
    store=SessionStore(db_path=str(tmp_path/'db.sqlite'))
    monkeypatch.setattr(gateway,'store',store)
    with TestClient(gateway.app) as client:
        frame=req('bypass',5,settings={'OverallStrength':0})
        first=post(client,frame)
        assert first['mode']=='bypass'
        assert post(client,frame)==first
        assert store.get('bypass')['kind']=='NOT_FOUND'
        post(client,{**frame,'settings':{'OverallStrength':1}},409)
        post(client,req('bypass',6))
        assert store.get('bypass')['frames']==1


def test_reset_clears_receipts_and_watermark(monkeypatch,tmp_path):
    store=SessionStore(db_path=str(tmp_path/'db.sqlite'))
    monkeypatch.setattr(gateway,'store',store)
    with TestClient(gateway.app) as client:
        post(client,req('reset',3))
        post(client,req('reset',2),409)
        assert store.reset('reset')
        post(client,req('reset',2))
        assert store.get('reset')['frames']==1


def test_concurrent_same_index_exactly_one_transition(monkeypatch,tmp_path):
    store=SessionStore(db_path=str(tmp_path/'db.sqlite'))
    monkeypatch.setattr(gateway,'store',store)
    frame=req('concurrent',0)
    with ThreadPoolExecutor(max_workers=8) as pool:
        def run(_):
            with TestClient(gateway.app) as client:
                r=client.post('/v1/frame',json=frame)
                return r.status_code
        codes=list(pool.map(run,range(16)))
    assert set(codes)<= {200,409}
    assert 200 in codes
    assert store.get('concurrent')['frames']==1


def test_fuzz_sequence_monotonic_and_replay(monkeypatch,tmp_path):
    store=SessionStore(db_path=str(tmp_path/'db.sqlite'))
    monkeypatch.setattr(gateway,'store',store)
    rng=random.Random(20261101)
    with TestClient(gateway.app) as client:
        last=-1
        captured={}
        for i in range(120):
            index=last+rng.choice([-2,-1,0,1,1,2,3])
            if index<0: index=0
            data=req('fuzz',index,seed=index%13)
            r=client.post('/v1/frame',json=data)
            no_null(r.json())
            if index>last:
                assert r.status_code==200,(i,index,last,r.text[:300])
                captured[index]=r.json();last=index
            elif index in captured:
                assert r.status_code==200
                assert r.json()==captured[index]
            else:
                assert r.status_code==409
        assert store.get('fuzz')['frames']==len(captured)


def test_journal_capacity_eviction_never_reexecutes(monkeypatch,tmp_path):
    store=SessionStore(db_path=str(tmp_path/'db.sqlite'))
    monkeypatch.setattr(gateway,'store',store)
    with TestClient(gateway.app) as client:
        first=req('bound',0,settings={'OverallStrength':0})
        post(client,first)
        for i in range(1,520):
            post(client,req('bound',i,settings={'OverallStrength':0}))
        assert post(client,first,409)['error']['fallback']=='REJECT'
        assert store.get('bound')['kind']=='NOT_FOUND'
        assert store._journal.conn.execute('SELECT COUNT(*) FROM receipts').fetchone()[0]<=512


def test_fingerprint_differs_with_output_controls():
    f1=FrameRequest.model_validate(req('x',1,settings={'LocalDetail':0}))
    f2=FrameRequest.model_validate(req('x',1,settings={'LocalDetail':1}))
    assert gateway.fingerprint(f1)!=gateway.fingerprint(f2)
