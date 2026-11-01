"""Live five-server v0.5.0 restart/replay/failure tests; loopback only."""
import argparse,base64,io,json,os,socket,subprocess,sys,tempfile,time
from pathlib import Path
import httpx,numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seed',type=int,required=True);o=ap.parse_args()
if not 0<=o.seed<2**63:ap.error('invalid seed')

def ports():
    used=[];nums={}
    for name in ('observer','controller','tone','renderer','gateway'):
        sk=socket.socket();sk.bind(('127.0.0.1',0));nums[name]=sk.getsockname()[1];used.append(sk)
    for sk in used:sk.close()
    return nums

def image():
    a=np.full((16,16,4),150,dtype=np.uint8);a[...,3]=255
    b=io.BytesIO();Image.fromarray(a,'RGBA').save(b,format='PNG');return base64.b64encode(b.getvalue()).decode('ascii')

def validate(v):
    if v is None:raise AssertionError('null')
    if isinstance(v,dict):
        for vv in v.values():validate(vv)
    if isinstance(v,list):
        for vv in v:validate(vv)

ports=ports(); procs={}; checks=[]
with tempfile.TemporaryDirectory(prefix='flexagx-v05-durable-') as temp:
    db=str(Path(temp)/'controller.sqlite3')
    def start(name):
        env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1'}
        if name=='controller':env['FLEXAGX_STATE_DB']=db
        if name=='gateway':
            env['GATEWAY_MODE']='distributed'
            for other in ('observer','controller','tone','renderer'):
                env[other.upper()+'_URL']='http://127.0.0.1:'+str(ports[other])
        procs[name]=subprocess.Popen([sys.executable,'-m','uvicorn',f'services.{name}:app','--host','127.0.0.1','--port',str(ports[name]),'--no-access-log'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def ready(c,name):
        for n in range(100):
            if procs[name].poll() is not None:raise AssertionError(f'{name} prematurely exited')
            try:
                x=c.get('http://127.0.0.1:'+str(ports[name])+'/health',timeout=1)
                if x.status_code==200:return
            except httpx.HTTPError:pass
            time.sleep(.1)
        raise AssertionError(f'{name} failed readiness')
    def stop(name):
        proc=procs[name];proc.terminate()
        try:proc.wait(timeout=6)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=6)
    try:
        with httpx.Client(timeout=20) as client:
            for n in ('observer','controller','tone','renderer','gateway'):start(n)
            for n in procs:ready(client,n)
            checks.append('start_all_five_services')
            base='http://127.0.0.1:'+str(ports['gateway'])
            state_url='http://127.0.0.1:'+str(ports['controller'])+'/v1/control/sessions/net-v05'
            frame={'session_id':'net-v05','frame_index':11,'image_png_base64':image(),'settings':{'Dithering':False,'LocalDetail':0}}
            r=client.post(base+'/v1/frame',json=frame);assert r.status_code==200,r.text[:300];first=r.json();validate(first)
            assert client.get(state_url).json()['frames']==1
            checks.append('distributed_initial_commit')
            r=client.post(base+'/v1/frame',json=frame);assert r.status_code==200 and r.json()==first
            assert client.get(state_url).json()['frames']==1
            checks.append('distributed_exact_replay')
            r=client.post(base+'/v1/frame',json={**frame,'settings':{'ColorTemp':5800}});assert r.status_code==409
            checks.append('distributed_conflicting_replay_rejected')
            stop('controller');start('controller');ready(client,'controller')
            r=client.post(base+'/v1/frame',json=frame);assert r.status_code==200 and r.json()==first
            assert client.get(state_url).json()['frames']==1
            checks.append('distributed_restart_durable_replay')
            r=client.post(base+'/v1/frame',json={**frame,'frame_index':12});assert r.status_code==200,r.text[:300]
            assert client.get(state_url).json()['frames']==2
            checks.append('distributed_post_restart_advancement')
            stop('renderer')
            r=client.post(base+'/v1/frame',json={**frame,'frame_index':13});assert r.status_code==502,r.text[:300]
            assert client.get(state_url).json()['frames']==2
            checks.append('downstream_failure_leaves_state_unchanged')
            start('renderer');ready(client,'renderer')
            r=client.post(base+'/v1/frame',json={**frame,'frame_index':13});assert r.status_code==200,r.text[:300]
            assert client.get(state_url).json()['frames']==3
            checks.append('retry_after_renderer_recovery')
    finally:
        for name in list(procs):
            if procs[name].poll() is None:stop(name)
assert len(checks)==8
result={'phase':'distributed_v05','seed':o.seed,'checks':len(checks),'passed':len(checks),'failed':0,
        'cases':[{'name':c,'status':'pass'} for c in checks],
        'network':'127.0.0.1 only','production_gate':'LOCKED'}
o.output.parent.mkdir(parents=True,exist_ok=True)
o.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'phase':'distributed_v05','checks':len(checks),'passed':len(checks),'failed':0}))
