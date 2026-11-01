"""Glue API: local in-process adapter or real HTTP service-to-service composition.

GATEWAY_MODE=local (default) invokes shared core functions for deterministic tests.
GATEWAY_MODE=distributed delegates to observer/control/tone/render microservers.
"""
import os
import httpx
from fastapi import FastAPI, HTTPException
from flexagx.contracts import FrameRequest, FrameResult, ToneRequest, ControlRequest, RenderRequest, TokenRequest, Observation, ControlResult, ToneResult, RenderResult
from flexagx.assurance import install_guards
from flexagx.compute import png_decode, png_encode, observe, make_lut, render_pixels
from flexagx.controller import SessionStore

app=FastAPI(title='FlexAgX Gateway — API / Microservers / Glue',version='0.3.0',
            description='Experimental CPU-source-equation port; not ReShade GPU certification')
install_guards(app)
store=SessionStore()
MODE=os.getenv('GATEWAY_MODE','local')
URLS={k:os.getenv(f'{k.upper()}_URL',f'http://{k}:8000') for k in ('observer','controller','tone','renderer')}

@app.get('/health')
def health(): return {'status':'ok','service':'gateway','mode':MODE}

@app.get('/v1/capabilities')
def capabilities():
    return {'version':'0.3.0','services':['observer','controller','tone','renderer','gateway'],
            'formats':['PNG/RGBA8'], 'output':['PNG/RGBA8'], 'state':'session-memory only',
            'backends':['cpu-numpy-scipy'], 'precision':'approximate',
            'production_gate':'LOCKED', 'fidelity':'not bit-exact with ReShade FX'}

@app.post('/v1/frame',response_model=FrameResult)
async def api_frame(req:FrameRequest):
    bypass=req.settings.OverallStrength<=0 and req.settings.DebugView==0
    if bypass:
        try:
            im=png_decode(req.image_png_base64)
        except (ValueError,OSError) as e: raise HTTPException(status_code=422,detail=str(e)) from e
        return FrameResult(image_png_base64=req.image_png_base64,width=im.shape[1],height=im.shape[0],
                           session_id=req.session_id,frame_index=req.frame_index,mode='bypass')
    if MODE=='local':
        try:
            im=png_decode(req.image_png_base64)
            obs=observe(im[...,:3],req.frame_index,req.settings)
            prepared=store.prepare(req.session_id,obs,req.settings,req.dt_ms)
            try:
                control=prepared.control
                tone=make_lut(control.gain,control.knee,req.settings.ShadowPreservation,
                              req.settings.InputEncoding,req.settings.OutputEncoding)
                result=render_pixels(im,req.settings,tone.lut,control.gain_ev)
                response=FrameResult(image_png_base64=png_encode(result),width=im.shape[1],height=im.shape[0],
                                   session_id=req.session_id,frame_index=req.frame_index,observation=obs,
                                   control=control,tone_validation=tone.model_dump(exclude={'lut'}),mode='processed')
                committed=store.commit(prepared.token)
                if not committed.committed:
                    raise HTTPException(status_code=409,detail='controller state changed during frame processing')
                return response
            finally:
                store.abort(prepared.token)
        except (ValueError,OSError) as e: raise HTTPException(status_code=422,detail=str(e)) from e
    if MODE!='distributed': raise HTTPException(status_code=503,detail='Unknown gateway mode; rejected')
    token=''
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            async def post(which,path,body):
                res=await client.post(URLS[which]+path,json=body)
                res.raise_for_status()
                return res.json()
            obs=await post('observer','/v1/observe',{
                'image_png_base64':req.image_png_base64,'frame_index':req.frame_index,'settings':req.settings.model_dump()})
            observation=Observation.model_validate(obs)
            prepared=await post('controller','/v1/control/prepare',ControlRequest(
                session_id=req.session_id,dt_ms=req.dt_ms,observation=observation,settings=req.settings).model_dump())
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
            committed=await post('controller','/v1/control/commit',TokenRequest(token=token).model_dump())
            if not committed.get('committed',False):
                raise HTTPException(status_code=409,detail='controller rejected frame commit')
            return response
    except (httpx.HTTPError, ValueError, KeyError) as e:
        raise HTTPException(status_code=502,detail='bounded microservice failure; frame rejected') from e
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
