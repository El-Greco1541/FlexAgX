"""End-to-end check with 5 actual HTTP servers; no production deployment."""
from __future__ import annotations
import base64, io, os, subprocess, sys, time
from pathlib import Path
import httpx
import numpy as np
from PIL import Image
PORTS={'observer':19441,'controller':19442,'tone':19443,'renderer':19444,'gateway':19445}
root=Path(__file__).resolve().parents[1]
processes=[]
try:
    for name,port in PORTS.items():
        env=os.environ.copy()
        if name=='gateway':
            env['GATEWAY_MODE']='distributed'
            for sub in ('observer','controller','tone','renderer'):
                env[sub.upper()+'_URL']=f'http://127.0.0.1:{PORTS[sub]}'
        command=[sys.executable,'-m','uvicorn',f'services.{name}:app','--host','127.0.0.1','--port',str(port),'--no-access-log']
        processes.append(subprocess.Popen(command,cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE))
    with httpx.Client(timeout=120) as client:
        for service,port in PORTS.items():
            for _ in range(100):
                try:
                    r=client.get(f'http://127.0.0.1:{port}/health',timeout=1)
                    if r.status_code==200: break
                except httpx.TransportError: pass
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError('Service quit during startup: '+service)
                time.sleep(.1)
            else: raise RuntimeError('Timed out waiting for '+service)
        image=np.zeros((12,16,4),dtype=np.uint8)
        image[...,0]=np.arange(16,dtype=np.uint8)[None,:]*10
        image[...,1]=np.arange(12,dtype=np.uint8)[:,None]*20
        image[...,2]=70
        image[...,3]=255
        buf=io.BytesIO(); Image.fromarray(image,'RGBA').save(buf,format='PNG')
        b64=base64.b64encode(buf.getvalue()).decode('ascii')
        request={'image_png_base64':b64,'session_id':'smoke', 'frame_index':0,
                 'dt_ms':16.67,'settings':{'LocalDetail':0,'Dithering':False}}
        r=client.post(f'http://127.0.0.1:{PORTS["gateway"]}/v1/frame',json=request)
        if r.status_code != 200: raise RuntimeError(str(r.status_code)+': '+r.text)
        out=r.json()
        assert out['mode']=='processed'
        assert out['tone_validation']['validation_passed']
        assert out['width']==16 and out['height']==12
        assert Image.open(io.BytesIO(base64.b64decode(out['image_png_base64']))).size==(16,12)
        print('SUCCESS: five independent HTTP servers; complete frame path, session, tone LUT and PNG output')
finally:
    for p in processes:
        if p.poll() is None: p.terminate()
    for p in processes:
        try: p.communicate(timeout=8)
        except subprocess.TimeoutExpired: p.kill();p.communicate()
