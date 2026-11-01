"""Test the actual ASGI application over loopback HTTP with bounded server lifespan."""
import argparse, json, os, socket, subprocess, sys, time, random, hashlib, math, signal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import httpx

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,required=True);p.add_argument('--frames',type=int,required=True);p.add_argument('--output',type=Path,required=True);o=p.parse_args()
    port=free_port();base=f'http://127.0.0.1:{port}';cases=[];errors=[];started=time.monotonic()
    flags={'stdout':subprocess.DEVNULL,'stderr':subprocess.DEVNULL}
    if os.name=='posix':flags['start_new_session']=True
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','correction_api.api:app','--host','127.0.0.1','--port',str(port),'--log-level','error'],cwd=Path(__file__).resolve().parents[1],**flags)
    try:
        with httpx.Client(timeout=httpx.Timeout(4.0),trust_env=False) as client:
            ready=False
            for _ in range(80):
                if proc.poll() is not None:raise RuntimeError('server exited before ready')
                try:
                    if client.get(base+'/health').status_code==200:ready=True;break
                except httpx.HTTPError:time.sleep(.05)
            if not ready:raise RuntimeError('server did not become ready')
            cases.append('health ready')
            r=client.get(base+'/v1/capabilities');assert r.status_code==200 and r.json()['production']=='LOCKED';cases.append('capability locked')
        rng=random.Random(o.seed^0xF00D)
        requests=[]
        for i in range(270):
            if i%9==0:
                requests.append(('/v1/correction/hue',{'stage':'output-gamut','a':0.0,'b':0.0},200))
            elif i%9==1:
                requests.append(('/v1/correction/hue',{'stage':'source-hue','a':0.0,'b':1e-7},200))
            elif i%9==2:
                requests.append(('/v1/correction/hue',{'stage':'curved-hue','a':rng.uniform(-4,4),'b':rng.uniform(-4,4)},200))
            elif i%9==3:
                requests.append(('/v1/correction/hue',{'stage':'invalid','a':0.,'b':0.},422))
            elif i%9==4:
                requests.append(('/v1/correction/hue',{'stage':'output-gamut','a':'NaN','b':0.},422))
            elif i%9==5:
                requests.append(('/v1/correction/histogram',{'bins':[0]*64,'valid_count':0,'white_count':0,'sample_count':0},200))
            elif i%9==6:
                requests.append(('/v1/correction/histogram',{'bins':[1]+[0]*63,'valid_count':1,'white_count':1,'sample_count':1},200))
            elif i%9==7:
                requests.append(('/v1/correction/histogram',{'bins':[1]+[0]*63,'valid_count':0,'white_count':0,'sample_count':0},422))
            else:
                requests.append(('/v1/correction/hue',{'stage':'output-gamut','a':rng.uniform(-8,8),'b':rng.uniform(-8,8)},200))
        def hit(req):
            path,payload,expected=req
            with httpx.Client(timeout=httpx.Timeout(8.0),trust_env=False) as c:
                r=c.post(base+path,json=payload)
                assert r.status_code==expected,(r.status_code,r.text[:200])
                assert 'null' not in r.text.lower() and 'nan' not in r.text.lower(),r.text[:200]
                if expected==422: assert r.json()['sentinel']['fallback']=='NO_MUTATION'
                return (path,expected)
        with ThreadPoolExecutor(max_workers=8) as exe:
            for i,v in enumerate(exe.map(hit,requests)):
                cases.append(f'http request {i} {v[1]}')
        with httpx.Client(timeout=4.0,trust_env=False) as c:
            r=c.get(base+'/health');assert r.status_code==200;cases.append('health after concurrent requests')
    except Exception as e:
        errors.append(type(e).__name__+': '+str(e)[:250])
    finally:
        if proc.poll() is None:
            if os.name=='posix':os.killpg(proc.pid,signal.SIGKILL)
            else:proc.kill()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:errors.append('server process did not exit')
    out={'phase':'live_http','seed':o.seed,'frames':o.frames,'status':'PASS' if not errors else 'FAIL','checks':len(cases),'passed':len(cases),'failed':0 if not errors else len(errors),'errors':errors,'case_ids':cases,'evidence_sha256':hashlib.sha256(('\n'.join(cases)).encode()).hexdigest(),'elapsed_seconds':round(time.monotonic()-started,3)}
    o.output.parent.mkdir(parents=True,exist_ok=True);o.output.write_text(json.dumps(out,allow_nan=False,indent=2)+'\n')
    print(json.dumps({'phase':'live_http','status':out['status'],'checks':len(cases),'failed':out['failed']}),flush=True)
    return 0 if not errors else 1
if __name__=='__main__':sys.exit(main())
