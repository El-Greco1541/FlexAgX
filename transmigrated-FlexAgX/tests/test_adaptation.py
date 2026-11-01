"""CT-004 deadband correctness; no change asserted for scene-cut policy."""
import random
from pathlib import Path
import pytest
from harness.adaptation_oracle import step_key,legacy_key_step,scene_cut_probe
from harness.source_audit import check_corrections
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('velocity',[-5.,-1.,0.,1.,5.])
@pytest.mark.parametrize('error',[-.03,-.01,0.,.01,.03])
def test_no_residual_motion_inside_deadband(velocity,error):
    r=step_key(-4.,velocity,-4.+error,16.667,.04)
    assert r.settled and r.velocity==0. and r.key==-4.

def test_zero_deadband_exact_target_also_stops():
    assert step_key(-4.,2.,-4.,16.667,0.).key==-4.

def test_old_drift_reproduced():
    assert legacy_key_step(-4.,2.,-3.99,16.667,.04).key!=-4.

def test_outside_band_identical_to_prior():
    rng=random.Random(2404)
    for _ in range(2000):
        x=rng.uniform(-12,5);v=rng.uniform(-2,2);sgn=rng.choice([-1,1])
        band=rng.uniform(0,.1);t=x+sgn*rng.uniform(.11,1)
        dt=rng.uniform(1,250);br=rng.uniform(.1,3);dark=rng.uniform(.1,5);rate=rng.uniform(.5,6)
        a=step_key(x,v,t,dt,band,br,dark,rate)
        b=legacy_key_step(x,v,t,dt,band,br,dark,rate)
        assert a.key==b.key and a.velocity==b.velocity

def test_source_mutation_detected():
    candidate=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
    upstream=(ROOT/'reference/FlexAgX_1.2.fx').read_text()
    assert check_corrections(candidate,upstream)==[]
    mutation=candidate.replace('if (abs(target - x) <= Deadband)','if (abs(target - x) < Deadband)',1)
    assert 'DEADBAND_VELOCITY_SETTLE_MISSING' in check_corrections(mutation,upstream)
    mutation=candidate.replace('                v = 0.0;\n            }\n            else','                v = v;\n            }\n            else',1)
    assert 'DEADBAND_VELOCITY_SETTLE_MISSING' in check_corrections(mutation,upstream)

def test_f29_timer_contract_only():
    assert scene_cut_probe(.8,.35,.08,30.)==(True,0.,True)
    assert scene_cut_probe(.8,.35,.0,30.)==(False,.03,False)
    assert scene_cut_probe(.1,.35,.08,30.)==(False,0.,False)

def test_f36_zero_strength_source_unchanged():
    source=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
    assert 'bool adapt = !FreezeExposure && darkGate > 0.0;' in source
    assert 'if (AutoExposureStrength <= 0.0)' in source
