"""Bounded, fail-closed subprocess harness. Research effect probes, not GPU execution."""
import argparse, hashlib, json, os, signal, subprocess, sys, time, uuid, shutil
from .toolchain_probe import toolchain
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MAX_OUTPUT=524288
MAX_RETAIN=8192
PHASES=('adaptation','temporal','source','hue','histogram','interface','metamorphic','torture','live_http')
LIMITS={'adaptation':35,'temporal':35,'source':25,'hue':50,'histogram':55,'interface':75,'metamorphic':40,'torture':80,'live_http':90}

class HarnessFailure(Exception):pass

def verify_evidence(p,phase,seed,frames,code):
    if code!=0:raise HarnessFailure(f'{phase}: exit {code}')
    if not p.is_file() or p.stat().st_size>2_097_152:raise HarnessFailure(f'{phase}: evidence missing or too large')
    try:d=json.loads(p.read_text())
    except (OSError,UnicodeError,ValueError) as e:raise HarnessFailure(f'{phase}: evidence missing/corrupt') from e
    if not isinstance(d,dict) or d.get('phase')!=phase or d.get('seed')!=seed or d.get('frames')!=frames:
        raise HarnessFailure(f'{phase}: wrong phase/seed/frames')
    if d.get('status')!='PASS' or type(d.get('checks')) is not int or d['checks']<=0 or d.get('passed')!=d['checks'] or d.get('failed')!=0 or d.get('errors')!=[]:
        raise HarnessFailure(f'{phase}: nonpassing or incoherent count evidence')
    cases=d.get('case_ids')
    if not isinstance(cases,list) or len(cases)!=d['checks'] or not all(type(v) is str and 0<len(v)<160 for v in cases):
        raise HarnessFailure(f'{phase}: case count/detail mismatch')
    expected=hashlib.sha256(('\n'.join(cases)).encode()).hexdigest()
    if d.get('evidence_sha256')!=expected:
        raise HarnessFailure(f'{phase}: evidence digest mismatch')
    return d

def bounded_child(argv,deadline=20,cwd=ROOT,output_budget=MAX_OUTPUT):
    if deadline<=0 or output_budget<=0:raise HarnessFailure('invalid subprocess limits')
    kw={'stdout':subprocess.PIPE,'stderr':subprocess.STDOUT,'cwd':cwd,'bufsize':0}
    if os.name=='posix':kw['start_new_session']=True
    p=subprocess.Popen(argv,**kw)
    try:
        # communicate accumulates output in RAM; only use it for the deliberately
        # small local selftests. Production phases have stdout capped by a
        # low-level pipe reader to prevent unbounded accumulation.
        import selectors
        select=selectors.DefaultSelector()
        select.register(p.stdout,selectors.EVENT_READ)
        out=bytearray();total=0;start=time.monotonic();eof=False
        while not eof:
            if time.monotonic()-start>deadline:raise HarnessFailure('child deadline exceeded')
            events=select.select(timeout=min(.20,max(.01,deadline-(time.monotonic()-start))))
            if not events:
                if p.poll() is not None:
                    # Still wait for EOF to drain final output.
                    pass
                continue
            for key,_ in events:
                block=os.read(key.fd,4096)
                if not block:
                    eof=True;break
                total+=len(block)
                if total>output_budget:raise HarnessFailure('child output budget exceeded')
                out.extend(block)
                if len(out)>MAX_RETAIN:del out[:-MAX_RETAIN]
        code=p.wait(timeout=3)
        return code,out.decode('utf-8','replace'),round(time.monotonic()-start,3)
    finally:
        if p.poll() is None:
            if os.name=='posix':os.killpg(p.pid,signal.SIGKILL)
            else:p.kill()
        try:p.wait(timeout=3)
        except subprocess.TimeoutExpired:pass
        try:select.close()
        except UnboundLocalError:pass

def run(seed=20261101,frames=1000,output_root=None,phases=PHASES):
    if not(0<=seed<=2**63-1 and 1<=frames<=2000):raise ValueError('seed or frame budget out of range')
    parent=Path(output_root or ROOT/'harness/results');parent.mkdir(parents=True,exist_ok=True)
    if parent.is_symlink():raise HarnessFailure('refuse symlinked evidence destination')
    run_id='fx-'+uuid.uuid4().hex[:12]
    location=parent/run_id;location.mkdir(exist_ok=False)
    results=[];issues=[];begin=time.monotonic()
    for phase in phases:
        if phase not in PHASES:raise HarnessFailure('unknown phase')
        output=location/(phase+'.json')
        command=[sys.executable,'-m','harness.live_http' if phase=='live_http' else 'harness.suites']
        if phase!='live_http':command.append(phase)
        command.extend(['--seed',str(seed),'--frames',str(frames),'--output',str(output)])
        try:
            code,tail,elapsed=bounded_child(command,LIMITS[phase])
            evidence=verify_evidence(output,phase,seed,frames,code)
            results.append({'phase':phase,'status':'PASS','checks':evidence['checks'],'passed':evidence['passed'],'failed':0,'elapsed_seconds':elapsed,'evidence_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        except (HarnessFailure,subprocess.TimeoutExpired,OSError) as e:
            issues.append({'phase':phase,'error':str(e)[:250]})
            results.append({'phase':phase,'status':'FAIL','checks':0,'passed':0,'failed':1,'elapsed_seconds':0,'evidence_sha256':'NOT_AVAILABLE'})
    checks=sum(x['checks'] for x in results);passed=sum(x['passed'] for x in results)
    status='PASS' if not issues and checks==passed else 'FAIL'
    report={'version':'0.4.0','subject':'Transmigrated FlexAgX effect — static and CPU correction probes','execution_scope':'NOT_GPU_OR_FX_COMPILER','seed':seed,'frames':frames,'run_id':run_id,'status':status,'checks':checks,'passed':passed,'failed':len(issues),'phases':results,'errors':issues,'elapsed_seconds':round(time.monotonic()-begin,3),'runtime_limits':{'child_output_bytes':MAX_OUTPUT,'retained_output_bytes':MAX_RETAIN,'per_suite_seconds':LIMITS},'toolchain':toolchain(),'unverified':['ReShade FX compiler acceptance','D3D11/D3D12/Vulkan/OpenGL GPU execution','original and corrected shader pixel identity','FA_State/FA_HistPrev boot-marker implementation requires native ReShade reload/cold-start acceptance','backend storage barrier semantics','F39/F40 gamut and encoding policy']}
    (location/'RUN_REPORT.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (parent/'LATEST_REPORT.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=20261101);parser.add_argument('--frames',type=int,default=1000);parser.add_argument('--output-dir',type=Path);opt=parser.parse_args()
    try:result=run(seed=opt.seed,frames=opt.frames,output_root=opt.output_dir)
    except (ValueError,HarnessFailure) as e:parser.error(str(e))
    print(json.dumps({k:result[k] for k in ('status','checks','passed','failed','frames','seed','run_id')}),flush=True)
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
