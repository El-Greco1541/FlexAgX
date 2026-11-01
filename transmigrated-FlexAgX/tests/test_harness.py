"""Deterministic harness contract tests, not shader/GPU tests."""
from pathlib import Path
import pytest
from harness.runner import verify_evidence,HarnessFailure
from harness.fixtures import histogram_source_model,lut_domain_index

def test_index_edges():
    assert lut_domain_index(0)==(0,1,0.)
    assert lut_domain_index(1.1)[:2]==(1023,1023) and abs(lut_domain_index(1.1)[2])<1e-10

def test_histogram_all_black():
    result=histogram_source_model([(0.,0.,0.)]*9,3,3,0)
    assert result[64]==result[65]==0

def test_harness_selftest():
    from harness.selftest import run
    assert len(run())==16

def test_harness_rejects_untrusted_counts(tmp_path):
    import json
    obj={'phase':'source','seed':3,'frames':3,'status':'PASS','checks':2,'passed':3,'failed':0,'errors':[],'evidence_sha256':'a'*64}
    f=tmp_path/'result.json';f.write_text(json.dumps(obj))
    with pytest.raises(HarnessFailure):verify_evidence(f,'source',3,3,0)
