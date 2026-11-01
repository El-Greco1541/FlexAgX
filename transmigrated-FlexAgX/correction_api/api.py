"""Local-only correctness probes; NOT an FX execution or image rendering service."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .models import HueRequest, HueResponse, HistogramRequest, HistogramResponse
from .glue import CorrectionCoordinator, CorrectionPorts

app = FastAPI(title='Transmigrated FlexAgX Correction Probes', version='0.1.0')
coordinator = CorrectionCoordinator(CorrectionPorts())

@app.exception_handler(RequestValidationError)
async def invalid_input(_: Request, __: RequestValidationError):
    # Prevent leaking request payloads; no null or nonfinite error values.
    return JSONResponse(status_code=422, content={
        'status':'REJECTED','sentinel':{
            'kind':'INVALID_INPUT','reason':'BOUNDARY_VALIDATION','fallback':'NO_MUTATION'}})

@app.exception_handler(Exception)
async def unexpected_failure(_: Request, __: Exception):
    return JSONResponse(status_code=500, content={
        'status':'REJECTED','sentinel':{
            'kind':'INTERNAL_FAILURE','reason':'REJECTED_FAIL_CLOSED','fallback':'NO_MUTATION'}})

@app.get('/health')
def health():
    return {'status':'ok','mode':'LOCAL_CORRECTION_PROBE','version':'0.1.0'}

@app.get('/v1/capabilities')
def capabilities():
    return {'status':'STAGED','kind':'CORRECTION_PROBE','rendering':'NOT_IMPLEMENTED',
            'gpu':'NOT_IMPLEMENTED','production':'LOCKED',
            'modules':['HUE_ORIGIN_GUARD','HISTOGRAM_PRECLEAR']}

@app.post('/v1/correction/hue', response_model=HueResponse)
def hue(request: HueRequest):
    return coordinator.hue(request)

@app.post('/v1/correction/histogram', response_model=HistogramResponse)
def histogram(request: HistogramRequest):
    return coordinator.histogram(request)
