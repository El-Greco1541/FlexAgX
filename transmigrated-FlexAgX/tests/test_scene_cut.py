"""CT-005 exact source witness and model tests; not GPU execution."""
from pathlib import Path
import random
import pytest
from harness.scene_cut_oracle import cut_step, old_cut_step, auto_strength_zero_contract
from harness.source_audit import check_corrections
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('ms',[100,101,110,150,200,250,1000])
def test_one_slow_frame_not_a_confirmed_cut(ms):
    assert old_cut_step(.8,.35,0,ms).fired
    out=cut_step(.8,.35,0,ms)
    assert not out.fired and out.seconds>0 and not out.update_reference

@pytest.mark.parametrize('ms',[100,150,250])
def test_two_frames_confirm_even_if_slow(ms):
    a=cut_step(.8,.35,0,ms)
    b=cut_step(.8,.35,a.seconds,16.667,key=-5,target=-1,velocity=1.)
    assert b.fired and b.seconds==0 and b.velocity==0 and b.key_delta==1.5

@pytest.mark.parametrize('ms',[1,16.667,50,99,250])
def test_reversion_aborts_pending(ms):
    a=cut_step(.8,.35,0,ms)
    b=cut_step(.1,.35,a.seconds,ms)
    assert not b.fired and b.update_reference and b.seconds==0

@pytest.mark.parametrize('ms',[100,250])
def test_strict_sensitivity_boundary(ms):
    assert cut_step(.35,.35,0,ms).seconds==0
    assert cut_step(.350001,.35,0,ms).seconds>0

def test_legacy_path_equivalent_given_prior_candidate():
    rng=random.Random(5105)
    for _ in range(4000):
        elapsed=rng.uniform(.001,.7);dt=rng.uniform(1,1000)
        a=rng.uniform(0,1);b=rng.uniform(.1,.6)
        assert cut_step(a,b,elapsed,dt)==old_cut_step(a,b,elapsed,dt)

def test_f36_zero_auto_strength_preserves_manual_offset():
    for value in [-2.,-1.,0.,1.,2.]:
        assert auto_strength_zero_contract(value,1.5,True)=={'applied_auto_ev':0.,'total_gain_ev':value,'tracker_advanced':True}

def test_f36_shader_source_remains_unchanged():
    text=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
    assert 'bool adapt = !FreezeExposure && darkGate > 0.0;' in text
    assert 'if (AutoExposureStrength <= 0.0)' in text
    assert 'appliedAutoEV = 0.0;' in text
    assert 'storedLambda = (AutoExposureStrength / 100.0)' in text

def test_structural_mutations_detected():
    text=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
    reference=(ROOT/'reference/FlexAgX_1.2.fx').read_text()
    assert check_corrections(text,reference)==[]
    bad=text.replace('if (hadCutCandidate && cutCount >= _FA_SCENE_CUT_SECONDS)','if (cutCount >= _FA_SCENE_CUT_SECONDS)',1)
    assert 'SCENE_CUT_TWO_OBSERVATIONS_MISSING' in check_corrections(bad,reference)
    bad=text.replace('bool hadCutCandidate = (cutCount > 0.0);','bool hadCutCandidate = true;',1)
    assert 'SCENE_CUT_TWO_OBSERVATIONS_MISSING' in check_corrections(bad,reference)
