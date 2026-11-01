from flexagx.assurance import install_guards
from fastapi import FastAPI, HTTPException
from flexagx.contracts import ObserveRequest, Observation
from flexagx.compute import png_decode, observe

app=FastAPI(title='FlexAgX Observer Microserver',version='0.3.0')

install_guards(app)

@app.get('/health')
def health(): return {'status':'ok','service':'observer'}

@app.post('/v1/observe',response_model=Observation)
def api_observe(req:ObserveRequest):
    try: return observe(png_decode(req.image_png_base64)[...,:3],req.frame_index,req.settings)
    except (ValueError,OSError) as e: raise HTTPException(status_code=422,detail=str(e)) from e
