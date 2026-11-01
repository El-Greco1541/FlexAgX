"""Independently exercise harness failure gates, then report a bounded test result."""
import json, sys, tempfile, hashlib, time
from pathlib import Path
from .runner import HarnessFailure,verify_evidence,bounded_child

def run():
    cases=[]
    with tempfile.TemporaryDirectory(prefix='fx-selftest-') as temp:
        base=Path(temp);ok={'phase':'source','seed':7,'frames':1,'status':'PASS','checks':3,'passed':3,'failed':0,'errors':[],'case_ids':['first','second','third'],'evidence_sha256':hashlib.sha256(b'first\nsecond\nthird').hexdigest()}
        p=base/'report.json';p.write_text(json.dumps(ok));assert verify_evidence(p,'source',7,1,0)['checks']==3;cases.append('valid evidence accepted')
        for field,value in [('status','FAIL'),('checks',0),('passed',2),('failed',1),('seed',8),('frames',2),('phase','other'),('evidence_sha256','xx'),('case_ids', ['first','second'])]:
            bad=dict(ok);bad[field]=value;p.write_text(json.dumps(bad))
            try:verify_evidence(p,'source',7,1,0);raise AssertionError('accepted corrupted '+field)
            except HarnessFailure:cases.append('rejected corrupted '+field)
        p.write_text('{broken')
        try:verify_evidence(p,'source',7,1,0);raise AssertionError('accepted malformed JSON')
        except HarnessFailure:cases.append('rejected malformed JSON')
        p.unlink()
        try:verify_evidence(p,'source',7,1,0);raise AssertionError('accepted missing evidence')
        except HarnessFailure:cases.append('rejected missing evidence')
        p.write_text(json.dumps(ok))
        try:verify_evidence(p,'source',7,1,1);raise AssertionError('accepted nonzero exit')
        except HarnessFailure:cases.append('rejected nonzero exit')
        try:bounded_child([sys.executable,'-c','import time;time.sleep(2)'],deadline=.2);raise AssertionError('timeout missed')
        except HarnessFailure:cases.append('killed timed-out child')
        try:bounded_child([sys.executable,'-c','print("x"*30000)'],deadline=3,output_budget=2048);raise AssertionError('output flood missed')
        except HarnessFailure:cases.append('killed over-output child')
        code,tail,secs=bounded_child([sys.executable,'-c','print("SAFE")'],deadline=3)
        assert code==0 and tail.strip()=='SAFE';cases.append('accepted bounded normal child')
    return cases

def main():
    items=run();report={'status':'PASS','tests':len(items),'passed':len(items),'failed':0,'cases':items}
    print(json.dumps(report,indent=2,allow_nan=False));return 0
if __name__=='__main__':sys.exit(main())
