from fastapi import FastAPI, HTTPException
from flexagx.contracts import ControlRequest, ControlResult, FrameResult, TokenRequest, PrepareResult, CommitResult, FrameReceiptQuery, FrameReceiptResult, FinalizeRequest, FinalizeResult, BypassRecordRequest
from flexagx.assurance import install_guards
from flexagx.controller import SessionStore

app=FastAPI(title='FlexAgX Controller Microserver',version='0.5.0')
install_guards(app)
store=SessionStore()

@app.get('/health')
def health(): return {'status':'ok','service':'controller'}

@app.post('/v1/control/step',response_model=ControlResult)
def api_step(req:ControlRequest):
    try: return store.step(req.session_id,req.observation,req.settings,req.dt_ms)
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e

@app.post('/v1/control/prepare',response_model=PrepareResult)
def api_prepare(req:ControlRequest):
    try: return store.prepare(req.session_id,req.observation,req.settings,req.dt_ms,req.frame_index,req.request_digest)
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e

@app.post('/v1/control/commit',response_model=CommitResult)
def api_commit(req:TokenRequest): return store.commit(req.token)

@app.post('/v1/control/abort',response_model=CommitResult)
def api_abort(req:TokenRequest): return store.abort(req.token)

@app.get('/v1/control/sessions/{session_id}')
def api_state(session_id:str):
    state=store.get(session_id)
    if isinstance(state,dict) and state.get('kind')=='NOT_FOUND': raise HTTPException(status_code=404,detail='Session not found')
    return state

@app.delete('/v1/control/sessions/{session_id}')
def api_reset(session_id:str): return {'reset':store.reset(session_id)}

@app.post('/v1/control/receipt',response_model=FrameReceiptResult)
def api_receipt(req:FrameReceiptQuery):
    try: return store.receipt(req.session_id,req.frame_index,req.request_digest)
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e

@app.post('/v1/control/finalize',response_model=FinalizeResult)
def api_finalize(req:FinalizeRequest):
    try: return store.finalize(req.token,req.response)
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e

@app.post('/v1/control/bypass',response_model=FrameResult)
def api_bypass(req:BypassRecordRequest):
    try: return store.record_bypass(req.session_id,req.frame_index,req.request_digest,req.response)
    except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e
