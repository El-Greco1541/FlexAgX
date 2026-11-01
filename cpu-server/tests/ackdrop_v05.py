"""Actual HTTP acknowledgment-loss simulation: controller durable commit then proxy 504."""
import argparse,base64,io,json,os,socket,subprocess,sys,tempfile,time
from pathlib import Path
import httpx,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--seed',type=int,required=True);opts=a.parse_args()
if not 0<=opts.seed<2**63:a.error('seed out of range')
ports={};reservations=[]
for name in ('observer','controller','tone','renderer','gateway','proxy'):
    sk=socket.socket();sk.bind(('127.0.0.1',0));ports[name]=sk.getsockname()[1];reservations.append(sk)
for sk in reservations:sk.close()
procs={}; checks=[]
with tempfile.TemporaryDirectory(prefix='flexagx-ackdrop-') as temp:
    def start(name):
        env={**os.environ,'PYTHONPATH':str(ROOT),'PYTHONDONTWRITEBYTECODE':'1','FLEXAGX_STATE_DB':str(Path(temp)/'controller.sqlite3')}
        if name=='proxy':env['ACKDROP_TARGET_CONTROLLER']='http://127.0.0.1:'+str(ports['controller'])
        if name=='gateway':
            env['GATEWAY_MODE']='distributed'
            for downstream in ('observer','controller','tone','renderer'):
                env[downstream.upper()+'_URL']='http://127.0.0.1:'+str(ports['proxy'] if downstream=='controller' else ports[downstream])
        module='tests.ackdrop_proxy_v05' if name=='proxy' else 'services.'+name
        procs[name]=subprocess.Popen([sys.executable,'-m','uvicorn',module+':app','--host','127.0.0.1','--port',str(ports[name]),'--no-access-log'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def stop():
        for proc in procs.values():
            if proc.poll() is None:proc.terminate()
        for proc in procs.values():
            try:proc.wait(timeout=6)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=6)
    try:
        with httpx.Client(timeout=20) as client:
            for n in ports:start(n)
            for name in ports:
                url='http://127.0.0.1:'+str(ports[name])+'/health'
                for i in range(100):
                    if procs[name].poll() is not None:raise AssertionError(name+' exited')
                    try:
                        status=client.get(url,timeout=1).status_code
                        if status in (200,404):break
                    except httpx.HTTPError: pass
                    time.sleep(.1)
                else:raise AssertionError(name+' startup exceeded deadline')
            checks.append('all_services_and_ackdrop_proxy_started')
            x=np.full((16,16,4),119,dtype=np.uint8);x[...,3]=255
            out=io.BytesIO();Image.fromarray(x,'RGBA').save(out,format='PNG')
            frame={'session_id':'ackdrop','frame_index':40,'image_png_base64':base64.b64encode(out.getvalue()).decode('ascii'),'settings':{'LocalDetail':0,'Dithering':False}}
            gateway='http://127.0.0.1:'+str(ports['gateway'])
            controller='http://127.0.0.1:'+str(ports['controller'])
            res=client.post(gateway+'/v1/frame',json=frame)
            assert res.status_code==200,res.text[:300]
            assert res.json()['frame_index']==40
            assert client.get(controller+'/v1/control/sessions/ackdrop').json()['frames']==1
            checks.append('lost_finalize_ack_recovers_durable_response')
            replay=client.post(gateway+'/v1/frame',json=frame)
            assert replay.status_code==200 and replay.json()==res.json()
            assert client.get(controller+'/v1/control/sessions/ackdrop').json()['frames']==1
            checks.append('ackdrop_replay_keeps_single_commit')
    finally:stop()
result={'phase':'ackdrop_v05','seed':opts.seed,'checks':len(checks),'passed':len(checks),'failed':0,'cases':[{'name':x,'status':'pass'} for x in checks],'production_gate':'LOCKED'}
opts.output.parent.mkdir(parents=True,exist_ok=True)
opts.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'phase':'ackdrop_v05','checks':len(checks),'passed':len(checks),'failed':0}))
