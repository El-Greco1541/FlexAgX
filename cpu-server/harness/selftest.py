"""Adversarial tests for the harness itself, not the product under test."""
import json
import os
from pathlib import Path
import sys
import tempfile
from .run_sentinel_harness import bounded,read_evidence,valid_json, PINNED_SHADER_SHA256,sha,ROOT

ENV={**os.environ,'PYTHONPATH':str(ROOT)}

def insist_raises(fn):
    try: fn()
    except (AssertionError,ValueError): return
    raise AssertionError('harness failed to reject invalid evidence')

def main():
    checks=[]
    assert sha(ROOT/'reference/FlexAgX_original.fx')==PINNED_SHADER_SHA256
    checks.append('pinned_source_integrity')
    insist_raises(lambda:valid_json({'unexpected':None}))
    insist_raises(lambda:valid_json({'unexpected':float('nan')}))
    insist_raises(lambda:valid_json({'unexpected':float('inf')}))
    checks.append('sentinel_and_finite_enforcement')
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'phase.json'
        payload={'phase':'validation','seed':42,'checks':1,'passed':1,'failed':0,
                 'cases':[{'name':'a','status':'pass'}]}
        p.write_text(json.dumps(payload))
        assert read_evidence(p,'validation',42)['checks']==1
        insist_raises(lambda:read_evidence(p,'metamorphic',42))
        insist_raises(lambda:read_evidence(p,'validation',41))
        payload['checks']=2;p.write_text(json.dumps(payload))
        insist_raises(lambda:read_evidence(p,'validation',42))
        payload['checks']=1;payload['cases'][0]['status']='fail';p.write_text(json.dumps(payload))
        insist_raises(lambda:read_evidence(p,'validation',42))
        payload['cases'][0]['status']='pass';payload['cases'].append({'name':'a','status':'pass'});
        payload['checks']=2;payload['passed']=2;p.write_text(json.dumps(payload))
        insist_raises(lambda:read_evidence(p,'validation',42))
        p.unlink(); insist_raises(lambda:read_evidence(p,'validation',42))
        checks.append('evidence_missing_counts_identity_and_staleness')
    out=bounded([sys.executable,'-c','import time; time.sleep(5)'],1,ENV)
    assert out['timed_out'] and out['seconds'] < 4,out
    checks.append('watchdog_kills_hung_child')
    out=bounded([sys.executable,'-c','import sys; sys.stdout.write("Z"*1200000); sys.stdout.flush()'],5,ENV)
    assert out['output_limit_exceeded'] and out['output_bytes'] <= 1200000 and len(out['output_tail']) <= 12288,out
    checks.append('unbounded_child_output_detected')
    out=bounded([sys.executable,'-c','print("ok")'],5,ENV)
    assert out['exit_code']==0 and 'ok' in out['output_tail'] and out['reader_closed'],out
    checks.append('normal_child_passes')
    print(json.dumps({'checks':checks,'passed':len(checks),'failed':0},allow_nan=False))

if __name__=='__main__': main()
