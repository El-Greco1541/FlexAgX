from fastapi import FastAPI, HTTPException
from flexagx.contracts import ControlRequest, ControlResult, TokenRequest, PrepareResult, CommitResult
from flexagx.assurance import install_guards
from flexagx.controller import SessionStore

app=FastAPI(title='FlexAgX Controller Microserver',version='0.3.0')
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
    try: return store.prepare(req.session_id,req.observation,req.settings,req.dt_ms)
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
