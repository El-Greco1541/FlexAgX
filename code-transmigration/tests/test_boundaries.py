"""Deterministic boundary, service-contract and local corpus probes."""
import base64
import io
import json
import random
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from transmigration.adapters import contracts,ReferenceCPUAdapter
from transmigration.api import app
from transmigration.glue import FrameRejected, FrameConflict


def frame(seed: int, *, size: int = 8, strength: float = 75):
    rng=random.Random(seed)
    pixels=np.asarray([rng.randint(0,255) for _ in range(size*size*4)],dtype=np.uint8).reshape(size,size,4)
    pixels[...,3]=255
    buf=io.BytesIO()
    Image.fromarray(pixels,'RGBA').save(buf,format='PNG')
    return contracts.FrameRequest(session_id=f'syn{seed}',frame_index=10,
        image_png_base64=base64.b64encode(buf.getvalue()).decode('ascii'),
        settings=contracts.Settings(OverallStrength=strength,Dithering=False))

@pytest.mark.parametrize('seed',range(32))
def test_seeded_frame_is_finite_and_replay_is_stable(make_engine,seed):
    engine=make_engine()
    req=frame(seed)
    r=engine.frame(req)
    assert r.mode=='processed'
    assert r.width==8 and r.height==8
    assert r.observation.sample_count>=0
    assert r.tone_validation['validation_passed'] is True
    assert r.model_dump(mode='json')==engine.frame(req).model_dump(mode='json')
    assert engine.store.get(req.session_id)['frames']==1
    result=ReferenceCPUAdapter().decode(r.image_png_base64)
    assert np.isfinite(result).all()
    assert result.min()>=0 and result.max()<=1

@pytest.mark.parametrize('seed',range(16))
def test_zero_strength_exact_encoded_passthrough(make_engine,seed):
    engine=make_engine()
    req=frame(seed, strength=0)
    result=engine.frame(req)
    assert result.image_png_base64==req.image_png_base64
    assert result.mode=='bypass'


def test_corrupted_encoded_frame_is_fail_closed(make_engine):
    req=contracts.FrameRequest(session_id='badimage',frame_index=3,image_png_base64='ABCD')
    engine=make_engine()
    with pytest.raises(FrameRejected):engine.frame(req)
    assert engine.store.get('badimage')['kind']=='NOT_FOUND'


def test_extra_unrecognized_field_rejected():
    value=frame(102).model_dump(mode='json')
    value['opaque_override']='ignored?'
    with TestClient(app) as client:
        r=client.post('/v1/frame',json=value)
        assert r.status_code==422
        assert r.json()['error']['kind']=='INVALID'
        assert 'null' not in r.text


def test_nan_numeric_value_rejected():
    value=frame(103).model_dump(mode='json')
    value['settings']['ExposureOffset']=float('nan')
    with TestClient(app) as client:
        r=client.post('/v1/frame',content=json.dumps(value),headers={'content-type':'application/json'})
        assert r.status_code==422
        assert r.json()['error']['kind']=='INVALID'
        assert 'null' not in r.text


def test_no_direct_mutating_controller_endpoints():
    routes={x.path for x in app.routes}
    assert '/v1/control/step' not in routes
    assert '/v1/control/commit' not in routes
    assert '/v1/control/finalize' not in routes
