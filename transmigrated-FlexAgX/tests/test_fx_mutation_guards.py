"""Deliberately corrupt sample source strings; prove that structural guards fail closed."""
from pathlib import Path
from harness.source_audit import check_corrections

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'shader/FlexAgX_transmigrated.fx').read_text()
UPSTREAM=(ROOT/'reference/FlexAgX_1.2.fx').read_text()

def test_source_audit_accepts_candidate():
    assert check_corrections(SOURCE,UPSTREAM)==[]

def test_source_audit_rejects_missing_preclear():
    bad=SOURCE.replace('pass FlexAgX_ClearHistogramPass','pass ClearPassDISABLED',1)
    assert 'PASS_ORDER_OR_CARDINALITY' in check_corrections(bad,UPSTREAM)

def test_source_audit_rejects_bad_clear_limit():
    bad=SOURCE.replace('if (id.x < 67u)','if (id.x < 66u)',1)
    assert 'CLEAR_COVERAGE' in check_corrections(bad,UPSTREAM)

def test_source_audit_rejects_missing_source_hue_guard():
    bad=SOURCE.replace('if (inputChroma >= 1.0e-4)','if (brokenChroma >= 1.0e-4)',1)
    assert 'SOURCE_HUE_GUARD' in check_corrections(bad,UPSTREAM)

def test_source_audit_rejects_missing_curved_guard():
    bad=SOURCE.replace('if (curvedChroma > 1.0e-6)','if (brokenChroma > 1.0e-6)',1)
    assert 'CURVED_HUE_GUARD' in check_corrections(bad,UPSTREAM)

def test_source_audit_rejects_missing_output_guard():
    bad=SOURCE.replace('if (C > 1.0e-6)','if (broken > 1.0e-6)',1)
    assert 'OUTPUT_HUE_GUARD' in check_corrections(bad,UPSTREAM)
