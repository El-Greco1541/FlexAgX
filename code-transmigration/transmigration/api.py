"""Local-only FastAPI facade for correctness-first modular rendition.

This is a separate experimental API, not a replacement for the stable gateway.
"""
from __future__ import annotations
import os
from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from .dependencies import check_reference
from .modules import STAGES, SERVICE_NAMES
from .adapters import ReferenceCPUAdapter, contracts, controller
from .glue import CorrectnessFirstGlue, FrameConflict, FrameRejected
from flexagx.assurance import install_guards

check_reference()
app = FastAPI(title='FlexAgX Code Transmigration — correctness-first',version='0.1.0',
              description='Research-only source-grounded CPU modular rendition; no ReShade GPU parity')
install_guards(app)
_backend = ReferenceCPUAdapter()
_store = controller.SessionStore(db_path=os.getenv('FLEXAGX_TRANSMIGRATION_DB',':memory:'))
_engine = CorrectnessFirstGlue(_store,_backend)

@app.get('/health')
def health():
    return {'status':'ok','stage':'RESEARCH_ONLY','production_gate':'LOCKED','version':'0.1.0'}

@app.get('/v1/modules')
def modules():
    return {'source_pass_count':len(STAGES),'services':list(SERVICE_NAMES),
            'stages':[asdict(s) for s in STAGES],
            'gpu_parity':'UNVERIFIED','dispatch':'SERIAL_CORRECTNESS_FIRST'}

@app.get('/v1/provenance')
def provenance():
    return {'reference':'reference/FlexAgX_1.2.fx',
            'sha256':'e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d',
            'upstream':'El-Greco1541/FlexAgX','version':'1.2',
            'license':'MIT','mode':'CPU_APPROXIMATION'}

@app.post('/v1/frame',response_model=contracts.FrameResult)
def frame(req:contracts.FrameRequest):
    try:
        return _engine.frame(req)
    except FrameConflict as exc:
        raise HTTPException(status_code=409,detail=str(exc)[:160]) from exc
    except FrameRejected as exc:
        raise HTTPException(status_code=422,detail=str(exc)[:160]) from exc
