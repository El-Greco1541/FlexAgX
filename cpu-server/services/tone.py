from flexagx.assurance import install_guards
from fastapi import FastAPI
from flexagx.contracts import ToneRequest, ToneResult
from flexagx.compute import make_lut
app=FastAPI(title='FlexAgX Tone-Curve Microserver',version='0.3.0')

install_guards(app)

@app.get('/health')
def health(): return {'status':'ok','service':'tone'}

@app.post('/v1/tone/build',response_model=ToneResult)
def api_build(req:ToneRequest):
    return make_lut(req.gain,req.knee,req.shadow_preservation,req.input_encoding,req.output_encoding)
