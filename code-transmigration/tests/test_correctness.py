import base64
import hashlib
import io
import json
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from transmigration.dependencies import check_reference, FX_REFERENCE, import_cpu_core
from transmigration.modules import STAGES,SERVICE_NAMES
from transmigration.adapters import ReferenceCPUAdapter,contracts
from transmigration.glue import FrameConflict,FrameRejected
from transmigration.api import app

def request(index=1,session='test-session',strength=100,payload='ok'):
    raw=np.zeros((8,8,4),dtype=np.uint8)
    raw[:,:,:3]=(64,128,255) if payload=='ok' else (128,64,32)
    raw[:,:,3]=255
    stream=io.BytesIO();Image.fromarray(raw,'RGBA').save(stream,format='PNG')
    return contracts.FrameRequest(session_id=session,frame_index=index,
      image_png_base64=base64.b64encode(stream.getvalue()).decode('ascii'),
      settings=contracts.Settings(OverallStrength=strength,Dithering=False))

def assert_no_nulls(value):
    if value is None: raise AssertionError('null found')
    if isinstance(value,dict):
        for v in value.values():assert_no_nulls(v)
    if isinstance(value,list):
        for v in value:assert_no_nulls(v)

def test_original_shader_unchanged():
    assert check_reference()
    assert hashlib.sha256(FX_REFERENCE.read_bytes()).hexdigest() == 'e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d'

def test_mapping_contains_exact_eight_fx_passes():
    source=FX_REFERENCE.read_text()
    assert len(STAGES)==8 and len(set(x.source_pass for x in STAGES))==8
    assert [x.order for x in STAGES]==list(range(1,9))
    for stage in STAGES:
        assert 'pass '+stage.source_pass in source
        assert stage.shader_entry in source
    assert set(SERVICE_NAMES)=={'observer','controller','tone','renderer','glue'}

def test_pipeline_valid_png(make_engine):
    e=make_engine();r=e.frame(request()); assert r.mode=='processed'
    assert r.width==8 and r.height==8
    assert r.observation.sample_count==16
    assert r.tone_validation['validation_passed']
    assert_no_nulls(r.model_dump(mode='json'))

def test_same_frame_replay_exact_and_no_second_commit(make_engine):
    e=make_engine();a=request(index=5)
    first=e.frame(a);before=e.store.get(a.session_id)
    second=e.frame(a);after=e.store.get(a.session_id)
    assert first.model_dump()==second.model_dump()
    assert before==after and before['frames']==1

def test_conflicting_frame_rejected(make_engine):
    e=make_engine();e.frame(request(index=2))
    with pytest.raises(FrameConflict):e.frame(request(index=2,payload='other'))
    assert e.store.get('test-session')['frames']==1

def test_reverse_sequence_rejected(make_engine):
    e=make_engine();e.frame(request(index=9))
    with pytest.raises(FrameConflict): e.frame(request(index=8))

def test_bypass_is_persisted_without_state_advance(make_engine):
    e=make_engine();req=request(index=4,strength=0)
    a=e.frame(req);b=e.frame(req)
    assert a.mode=='bypass' and a.image_png_base64==req.image_png_base64
    assert a.model_dump()==b.model_dump()
    assert e.store.get('test-session')['kind']=='NOT_FOUND'

def test_sqlite_restart_exact_replay(make_engine):
    req=request(index=15)
    first=make_engine(persistent=True).frame(req)
    recovered=make_engine(persistent=True)
    second=recovered.frame(req)
    assert first.model_dump()==second.model_dump()
    assert recovered.store.get('test-session')['frames']==1

def test_failure_does_not_commit(make_engine):
    class BrokenRenderer(ReferenceCPUAdapter):
        def render(self,*args,**kwargs):raise ValueError('forced renderer failure')
    e=make_engine(ports=BrokenRenderer())
    with pytest.raises(FrameRejected):e.frame(request(index=3))
    assert e.store.get('test-session')['kind']=='NOT_FOUND'

def test_api_advertises_explicit_stage_contract():
    with TestClient(app) as c:
        response=c.get('/v1/modules')
        assert response.status_code==200
        data=response.json()
        assert data['source_pass_count']==8
        assert data['gpu_parity']=='UNVERIFIED'
        assert_no_nulls(data)

def test_api_invalid_request_returns_no_null():
    with TestClient(app) as c:
        response=c.post('/v1/frame',json={'session_id':'bad','frame_index':1,'image_png_base64':None})
        assert response.status_code==422
        assert_no_nulls(response.json())
        assert response.json()['error']['kind']=='INVALID'

def test_api_replay_and_conflict():
    req=request(index=72,session='api-seq').model_dump(mode='json')
    with TestClient(app) as c:
        a=c.post('/v1/frame',json=req); b=c.post('/v1/frame',json=req)
        assert a.status_code==200 and b.status_code==200 and a.json()==b.json()
        changed=request(index=72,session='api-seq',payload='other').model_dump(mode='json')
        reject=c.post('/v1/frame',json=changed)
        assert reject.status_code==409
        assert_no_nulls(reject.json())
