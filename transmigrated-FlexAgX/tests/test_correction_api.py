import json, math, random
import pytest
from fastapi.testclient import TestClient
from correction_api.api import app
from correction_api.models import HueRequest,HistogramRequest
from correction_api.modules import safe_hue,clear_and_accumulate
from correction_api.glue import CorrectionCoordinator, CorrectionPorts

client=TestClient(app)

def payload(**kw):
    return {'stage':'output-gamut','a':0.0,'b':0.0,**kw}

@pytest.mark.parametrize('stage',['source-hue','curved-hue','output-gamut'])
def test_origin_guard(stage):
    x=client.post('/v1/correction/hue',json={'stage':stage,'a':0.0,'b':0.0})
    assert x.status_code==200
    v=x.json()
    assert v['status']=='SENTINEL' and v['guarded'] is True
    assert v['angle_rad']==0.0 and v['reason']=='ACHROMATIC_FALLBACK'

@pytest.mark.parametrize('a,b',[(1.0,0.0),(0.0,1.0),(-1.0,1.0),(-1.0,-1.0),(.2,-.4)])
def test_nonzero_angle_matches_reference(a,b):
    r=client.post('/v1/correction/hue',json={'stage':'output-gamut','a':a,'b':b})
    assert r.status_code==200
    assert abs(r.json()['angle_rad']-math.atan2(b,a))<1e-12

@pytest.mark.parametrize('value',[None,float('nan'),float('inf'),1e100,'not a number'])
def test_boundary_rejection(value):
    # Non-finite tokens are deliberately invalid JSON; send raw bytes rather than
    # invoking the HTTP client's strict JSON serializer.
    if isinstance(value,float) and not math.isfinite(value):
        token = 'NaN' if math.isnan(value) else 'Infinity'
        resp=client.post('/v1/correction/hue',content='{"stage":"output-gamut","a":'+token+',"b":0.0}',headers={'content-type':'application/json'})
    else:
        resp=client.post('/v1/correction/hue',json={'stage':'output-gamut','a':value,'b':0.0})
    assert resp.status_code==422
    assert 'null' not in resp.text.lower() and 'nan' not in resp.text.lower()
    assert resp.json()['sentinel']['fallback']=='NO_MUTATION'

def test_histogram_reset_independent_calls():
    a=HistogramRequest(bins=[3]+[0]*63,valid_count=3,white_count=1,sample_count=5)
    b=HistogramRequest(bins=[0]*63+[7],valid_count=7,white_count=0,sample_count=7)
    first=clear_and_accumulate(a);second=clear_and_accumulate(b)
    assert first.counters[0]==3 and second.counters[0]==0
    assert second.counters[63]==7 and second.counters[64:]==[7,0,7]

def test_histogram_population_rejection():
    req={'bins':[0]*64,'valid_count':1,'white_count':0,'sample_count':1}
    bad=client.post('/v1/correction/histogram',json=req)
    assert bad.status_code==422
    assert bad.json()['status']=='REJECTED'

def test_histogram_output_no_null():
    req={'bins':[0]*64,'valid_count':0,'white_count':0,'sample_count':0}
    r=client.post('/v1/correction/histogram',json=req)
    assert r.status_code==200 and r.json()['cleared_first']
    assert None not in r.json().values()
    assert len(r.json()['counters'])==67

def test_injected_port():
    calls=[]
    def other_hue(q):
        calls.append(q.stage)
        return safe_hue(q)
    c=CorrectionCoordinator(CorrectionPorts(hue=other_hue))
    x=c.hue(HueRequest(stage='source-hue',a=0.0,b=0.0))
    assert calls==['source-hue'] and x.guarded

def test_bad_endpoint_has_no_null():
    r=client.post('/v1/correction/hue',json={'stage':'nope','a':0.0,'b':0.0})
    assert r.status_code==422
    assert 'null' not in r.text

def test_256_deterministic_fuzz_cases():
    rng=random.Random(125145)
    for _ in range(256):
        a=rng.uniform(-8.0,8.0);b=rng.uniform(-8.0,8.0)
        r=safe_hue(HueRequest(stage='output-gamut',a=a,b=b))
        assert math.isfinite(r.angle_rad)
        assert -math.pi<=r.angle_rad<=math.pi
        assert math.isfinite(r.chroma)

def test_256_histograms_with_fresh_zero_baseline():
    rng=random.Random(813)
    for _ in range(256):
        bins=[rng.randrange(0,15) for _ in range(64)]
        v=sum(bins)
        req=HistogramRequest(bins=bins,valid_count=v,white_count=rng.randrange(v+1),sample_count=v+rng.randrange(10))
        got=clear_and_accumulate(req).counters
        assert got[:64]==bins and got[64]==v

def test_info_is_non_deployment():
    x=client.get('/v1/capabilities').json()
    assert x['rendering']=='NOT_IMPLEMENTED' and x['production']=='LOCKED'


def test_source_hue_threshold_boundary():
    # Source chooses defined atan2 at exactly 1e-4, unlike curved/output stages.
    from correction_api.models import HueRequest
    x=safe_hue(HueRequest(stage='source-hue',a=0.0001,b=0.0))
    assert x.status=='OK' and not x.guarded
    y=safe_hue(HueRequest(stage='curved-hue',a=0.000001,b=0.0))
    assert y.status=='SENTINEL' and y.guarded

def test_minimal_histogram_and_large_bounded_population():
    req=HistogramRequest(bins=[2_000_000]+[0]*63,valid_count=2_000_000,white_count=0,sample_count=2_000_000)
    got=clear_and_accumulate(req)
    assert got.counters[0]==2_000_000 and len(got.counters)==67

def test_invalid_counter_type_rejected():
    payload={'bins':[0]*64,'valid_count':0,'white_count':0,'sample_count':0}
    payload['bins'][13]=False
    r=client.post('/v1/correction/histogram',json=payload)
    assert r.status_code==422 and r.json()['sentinel']['fallback']=='NO_MUTATION'

def test_response_contains_no_null_sentinels():
    def walk(x):
        assert x is not None
        if isinstance(x,dict):
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    examples=[
        client.post('/v1/correction/hue',json={'stage':'source-hue','a':0.,'b':0.}).json(),
        client.post('/v1/correction/histogram',json={'bins':[0]*64,'valid_count':0,'white_count':0,'sample_count':0}).json(),
        client.post('/v1/correction/hue',json={'stage':'source-hue','a':None,'b':0.}).json(),
    ]
    for x in examples:walk(x)
