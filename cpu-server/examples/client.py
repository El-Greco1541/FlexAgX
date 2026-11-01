"""Usage: python examples/client.py input.png output.png [gateway_url]"""
import base64, sys
from pathlib import Path
import httpx

if len(sys.argv)<3:
    raise SystemExit(__doc__)
input_path,output_path=map(Path,sys.argv[1:3]); url=sys.argv[3] if len(sys.argv)>3 else 'http://127.0.0.1:8080'
body={'session_id':'example','frame_index':0,'dt_ms':16.6667,
      'image_png_base64':base64.b64encode(input_path.read_bytes()).decode('ascii'),
      'settings':{'LocalDetail':20.0}}
r=httpx.post(url+'/v1/frame',json=body,timeout=120);r.raise_for_status()
data=r.json();output_path.write_bytes(base64.b64decode(data['image_png_base64']))
print({'output':str(output_path),'mode':data['mode'],'control':data.get('control'),'tone':data.get('tone_validation')})
