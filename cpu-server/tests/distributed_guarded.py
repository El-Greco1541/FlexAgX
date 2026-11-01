"""Live five-process smoke plus renderer-loss rollback and explicit sentinel errors."""
import base64
import io
import os
import argparse
import json
import socket
from pathlib import Path
import subprocess
import sys
import time
import httpx
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
def reserve_ephemeral_ports():
    ports={}
    reservations=[]
    for service in ('observer','controller','tone','renderer','gateway'):
        bound=socket.socket()
        bound.bind(('127.0.0.1',0))
        ports[service]=bound.getsockname()[1]
        reservations.append(bound)
    for bound in reservations: bound.close()
    return ports

PORTS=reserve_ephemeral_ports()
procs={}
checks=[]
arguments=argparse.ArgumentParser()
arguments.add_argument('--output',type=Path,required=True)
arguments.add_argument('--seed',type=int,required=True)
opts=arguments.parse_args()
if not 0 <= opts.seed <= 2**63-1: arguments.error('seed out of range')


def req_image():
    a=np.zeros((16,16,4),dtype=np.uint8);a[...,:3]=110;a[...,3]=255
    out=io.BytesIO();Image.fromarray(a,'RGBA').save(out,format='PNG')
    return base64.b64encode(out.getvalue()).decode('ascii')


def no_null(data):
    if data is None: raise AssertionError('null JSON found')
    if isinstance(data,dict):
        for v in data.values():no_null(v)
    if isinstance(data,list):
        for v in data:no_null(v)


try:
    for service,port in PORTS.items():
        env={**os.environ,'PYTHONPATH':str(ROOT)}
        if service=='gateway':
            env['GATEWAY_MODE']='distributed'
            for downstream in ('observer','controller','tone','renderer'):
                env[downstream.upper()+'_URL']=f'http://127.0.0.1:{PORTS[downstream]}'
        procs[service]=subprocess.Popen([sys.executable,'-m','uvicorn',f'services.{service}:app',
            '--host','127.0.0.1','--port',str(port),'--no-access-log'],cwd=ROOT,env=env,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    with httpx.Client(timeout=25.0) as client:
        for name,port in PORTS.items():
            for trial in range(100):
                try:
                    r=client.get(f'http://127.0.0.1:{port}/health',timeout=1.0)
                    if r.status_code==200 and r.json().get('service')==name and procs[name].poll() is None:break
                except httpx.TransportError:pass
                if procs[name].poll() is not None:raise AssertionError('service exited')
                time.sleep(.1)
            else:raise AssertionError('service startup timeout')
        checks.append('all_five_services_started')
        request={'image_png_base64':req_image(),'session_id':'txn-guard','frame_index':1,
                 'settings':{'LocalDetail':0,'Dithering':False}}
        gateway=f'http://127.0.0.1:{PORTS["gateway"]}'
        controller=f'http://127.0.0.1:{PORTS["controller"]}'
        r=client.post(gateway+'/v1/frame',json=request)
        assert r.status_code==200,r.text[:300];no_null(r.json())
        checks.append('distributed_success_and_no_null')
        state=client.get(controller+'/v1/control/sessions/txn-guard').json()
        assert state['frames']==1
        procs['renderer'].terminate();procs['renderer'].wait(timeout=6)
        request['frame_index']=2
        r=client.post(gateway+'/v1/frame',json=request)
        assert r.status_code==502,r.text[:300];no_null(r.json())
        assert r.json()['error']['fallback']=='REJECT'
        checks.append('renderer_loss_fails_closed')
        state=client.get(controller+'/v1/control/sessions/txn-guard').json()
        assert state['frames']==1,'failed frame advanced committed state'
        checks.append('renderer_loss_did_not_advance_controller_state')
        results={'phase':'distributed_guarded','seed':opts.seed,'checks':len(checks),
                 'passed':len(checks),'failed':0,'cases':[{'name':c,'status':'pass'} for c in checks],
                 'network':'127.0.0.1 only','ports':{'kind':'NOT_APPLICABLE','reason':'ephemeral ports are nonportable run metadata','fallback':'SKIP'}}
        opts.output.parent.mkdir(parents=True,exist_ok=True)
        opts.output.write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'phase':'distributed_guarded','checks':len(checks),'passed':len(checks),'failed':0}))
finally:
    for p in procs.values():
        if p.poll() is None:p.terminate()
    for p in procs.values():
        try:p.wait(timeout=6)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=6)
