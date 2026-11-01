"""Glue API: local in-process adapter or real HTTP service-to-service composition.

GATEWAY_MODE=local (default) invokes shared core functions for deterministic tests.
GATEWAY_MODE=distributed delegates to observer/control/tone/render microservers.
"""
import os
import hashlib
import json
import httpx
from fastapi import FastAPI, HTTPException
from flexagx.contracts import FrameRequest, FrameResult, ToneRequest, ControlRequest, RenderRequest, TokenRequest, FrameReceiptQuery, FinalizeRequest, FrameReceiptResult, BypassRecordRequest, Observation, ControlResult, ToneResult, RenderResult
from flexagx.assurance import install_guards
from flexagx.compute import png_decode, png_encode, observe, make_lut, render_pixels
from flexagx.controller import SessionStore

app=FastAPI(title='FlexAgX Gateway — API / Microservers / Glue',version='0.5.0',
            description='Experimental CPU-source-equation port; not ReShade GPU certification')
install_guards(app)
store=SessionStore()
MODE=os.getenv('GATEWAY_MODE','local')
URLS={k:os.getenv(f'{k.upper()}_URL',f'http://{k}:8000') for k in ('observer','controller','tone','renderer')}

@app.get('/health')
def health(): return {'status':'ok','service':'gateway','mode':MODE}

@app.get('/v1/capabilities')
def capabilities():
    return {'version':'0.5.0','services':['observer','controller','tone','renderer','gateway'],
            'formats':['PNG/RGBA8'], 'output':['PNG/RGBA8'], 'state':'session-memory only',
            'backends':['cpu-numpy-scipy'], 'precision':'approximate',
            'production_gate':'LOCKED', 'fidelity':'not bit-exact with ReShade FX'}

def fingerprint(req):
    return hashlib.sha256(json.dumps(req.model_dump(mode='json'),sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()

@app.post('/v1/frame',response_model=FrameResult)
async def api_frame(req:FrameRequest):
    digest=fingerprint(req)
    query=FrameReceiptQuery(session_id=req.session_id,frame_index=req.frame_index,request_digest=digest)
    if MODE=='local':
        try: existing=store.receipt(req.session_id,req.frame_index,digest)
        except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e
        if existing.status=='REPLAY': return existing.response
    elif MODE=='distributed':
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as preflight:
                r=await preflight.post(URLS['controller']+'/v1/control/receipt',json=query.model_dump())
                if r.status_code==409: raise HTTPException(status_code=409,detail='duplicate/stale/conflicting frame')
                r.raise_for_status()
                prior=FrameReceiptResult.model_validate(r.json())
                if prior.status=='REPLAY': return prior.response
        except httpx.HTTPError as e: raise HTTPException(status_code=502,detail='controller receipt lookup failed') from e
    else: raise HTTPException(status_code=503,detail='invalid gateway mode')
    bypass=req.settings.OverallStrength<=0 and req.settings.DebugView==0
    if bypass:
        try:
            im=png_decode(req.image_png_base64)
        except (ValueError,OSError) as e: raise HTTPException(status_code=422,detail=str(e)) from e
        response=FrameResult(image_png_base64=req.image_png_base64,width=im.shape[1],height=im.shape[0],
                             session_id=req.session_id,frame_index=req.frame_index,mode='bypass')
        if MODE=='local':
            try: return store.record_bypass(req.session_id,req.frame_index,digest,response)
            except ValueError as e: raise HTTPException(status_code=409,detail=str(e)) from e
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                r=await client.post(URLS['controller']+'/v1/control/bypass',json=BypassRecordRequest(
                    session_id=req.session_id,frame_index=req.frame_index,request_digest=digest,response=response).model_dump())
                if r.status_code==409: raise HTTPException(status_code=409,detail='bypass frame conflict')
                r.raise_for_status()
                return FrameResult.model_validate(r.json())
        except httpx.HTTPError as e:
            # Resolve lost acknowledgment by looking up the durable response.
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as recovery:
                    r=await recovery.post(URLS['controller']+'/v1/control/receipt',json=query.model_dump())
                    if r.status_code==200:
                        receipt=FrameReceiptResult.model_validate(r.json())
                        if receipt.status=='REPLAY': return receipt.response
            except (httpx.HTTPError,ValueError): pass
            raise HTTPException(status_code=502,detail='bypass commit uncertain; inspect receipt before retry') from e
    if MODE=='local':
        try:
            im=png_decode(req.image_png_base64)
            obs=observe(im[...,:3],req.frame_index,req.settings)
            prepared=store.prepare(req.session_id,obs,req.settings,req.dt_ms,req.frame_index,digest)
            try:
                control=prepared.control
                tone=make_lut(control.gain,control.knee,req.settings.ShadowPreservation,
                              req.settings.InputEncoding,req.settings.OutputEncoding)
                result=render_pixels(im,req.settings,tone.lut,control.gain_ev)
                response=FrameResult(image_png_base64=png_encode(result),width=im.shape[1],height=im.shape[0],
                                   session_id=req.session_id,frame_index=req.frame_index,observation=obs,
                                   control=control,tone_validation=tone.model_dump(exclude={'lut'}),mode='processed')
                committed=store.finalize(prepared.token,response)
                if not committed.committed:
                    raise HTTPException(status_code=409,detail='controller state changed during frame processing')
                return response
            finally:
                store.abort(prepared.token)
        except ValueError as e:
            status=409 if any(term in str(e).lower() for term in ('pending','replay','stale','session capacity','frame index','committed')) else 422
            raise HTTPException(status_code=status,detail=str(e)) from e
        except OSError as e: raise HTTPException(status_code=422,detail=str(e)) from e
    if MODE!='distributed': raise HTTPException(status_code=503,detail='Unknown gateway mode; rejected')
    token=''
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            async def post(which,path,body):
                res=await client.post(URLS[which]+path,json=body)
                if res.status_code==409: raise HTTPException(status_code=409,detail='controller sequence/transaction conflict')
                res.raise_for_status()
                return res.json()
            obs=await post('observer','/v1/observe',{
                'image_png_base64':req.image_png_base64,'frame_index':req.frame_index,'settings':req.settings.model_dump()})
            observation=Observation.model_validate(obs)
            prepared=await post('controller','/v1/control/prepare',ControlRequest(
                session_id=req.session_id,dt_ms=req.dt_ms,observation=observation,settings=req.settings,frame_index=req.frame_index,request_digest=digest).model_dump())
            token=prepared['token']
            ctrl=ControlResult.model_validate(prepared['control'])
            tone_data=await post('tone','/v1/tone/build',ToneRequest(
                gain=ctrl.gain,knee=ctrl.knee,shadow_preservation=req.settings.ShadowPreservation,
                input_encoding=req.settings.InputEncoding,output_encoding=req.settings.OutputEncoding).model_dump())
            tone=ToneResult.model_validate(tone_data)
            result_data=await post('renderer','/v1/render',RenderRequest(
                image_png_base64=req.image_png_base64,settings=req.settings,
                gain_ev=ctrl.gain_ev,lut=tone.lut).model_dump())
            result=RenderResult.model_validate(result_data)
            response=FrameResult(**result.model_dump(),session_id=req.session_id,frame_index=req.frame_index,
                               observation=observation,control=ctrl,
                               tone_validation=tone.model_dump(exclude={'lut'}),mode='processed')
            committed=await post('controller','/v1/control/finalize',FinalizeRequest(token=token,response=response).model_dump())
            if not committed.get('committed',False):
                raise HTTPException(status_code=409,detail='controller rejected frame commit')
            return response
    except (httpx.HTTPError, ValueError, KeyError) as e:
        # A lost finalize acknowledgment might hide a successful durable commit.
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(2.0)) as recovery:
                check=await recovery.post(URLS['controller']+'/v1/control/receipt',json=query.model_dump())
                if check.status_code==200:
                    receipt=FrameReceiptResult.model_validate(check.json())
                    if receipt.status=='REPLAY': return receipt.response
        except (httpx.HTTPError,ValueError): pass
        raise HTTPException(status_code=502,detail='bounded microservice failure; inspect receipt before retry') from e
    finally:
        if token:
            try:
                async with httpx.AsyncClient(timeout=2.0) as cleanup:
                    await cleanup.post(URLS['controller']+'/v1/control/abort',json={'token':token})
            except httpx.HTTPError:
                pass  # bounded 30-second pending token expiration is the fallback

@app.get('/v1/sessions/{session_id}')
def get_session(session_id:str):
    if MODE!='local': raise HTTPException(status_code=501,detail='Query controller directly in distributed mode')
    state=store.get(session_id)
    if isinstance(state,dict) and state.get('kind')=='NOT_FOUND': raise HTTPException(status_code=404,detail='Unknown session')
    return state

@app.delete('/v1/sessions/{session_id}')
def reset_session(session_id:str):
    if MODE!='local': raise HTTPException(status_code=501,detail='Reset via controller in distributed mode')
    return {'reset':store.reset(session_id)}
