"""F18/F32 source-level regression probes. Cannot certify ReShade GPU behavior."""
from pathlib import Path
import pytest
from harness.temporal_oracle import temporal_marker,temporal_valid,normalized_reference
from harness.source_audit import check_corrections
ROOT=Path(__file__).resolve().parents[1]
FX=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
ORIGINAL=(ROOT/'reference/FlexAgX_1.2.fx').read_text()
STATE=(-5.,0.,0.5,0.)
META=(.2,1.,.1,.3)

def test_validity_marker_consecutive_and_restart():
    assert temporal_valid(temporal_marker(19),20,STATE,META)
    assert not temporal_valid(temporal_marker(19),21,STATE,META)
    assert not temporal_valid((0.,0.,0.,0.),20,STATE,META)

def test_wrap_and_large_u32_frame():
    assert temporal_valid(temporal_marker(0xffffffff),0,STATE,META)
    assert temporal_valid(temporal_marker(0xfffffffe),0xffffffff,STATE,META)
    assert not temporal_valid(temporal_marker(0xfffffffd),0xffffffff,STATE,META)

def test_corrupt_prior_state_rejected():
    for i in range(4):
        c=list(STATE);c[i]=float('nan')
        assert not temporal_valid(temporal_marker(12),13,c,META)
        c=list(META);c[i]=float('inf')
        assert not temporal_valid(temporal_marker(12),13,STATE,c)

def test_cold_scene_reference_baseline():
    baseline=normalized_reference([12]+[0]*63)
    assert baseline[0]==1.0 and all(x==0 for x in baseline[1:])
    assert normalized_reference([0]*64)==[0.0]*64

def test_source_controls_prev_histogram_access():
    assert check_corrections(FX,ORIGINAL)==[]
    text=FX[FX.index('void FlexAgX_State('):]
    assert text.index('FA_ColdStart = valid ? 0 : 1;')<text.index('tex2Dfetch(FA_HistPrevStorage')
    assert text.index('FA_PrevSh[lane] = currentNorm;')<text.index('tex2Dfetch(FA_HistPrevStorage')

def test_mutation_missing_boot_stamp_rejected():
    altered=FX.replace('FA_ColdStart = valid ? 0 : 1;', 'FA_ColdStart = 0;',1)
    assert 'COLD_MARKER_MISSING' in check_corrections(altered,ORIGINAL)

def test_mutation_boot_commit_order_rejected():
    altered=FX.replace('tex2Dstore(FA_TemporalBootStorage, int2(0, 0),','tex2Dstore(FA_TemporalBootStorage, int2(0, 1),',1)
    assert 'BOOT_COMMIT_ORDER_INVALID' in check_corrections(altered,ORIGINAL)

def test_warmup_reinitialization_on_gap():
    assert temporal_valid(temporal_marker(100),101,STATE,META)
    assert not temporal_valid(temporal_marker(100),106,STATE,META)
