"""Typed sentinel protocol, finite error results, limited input budgets, fail-closed exits."""
from __future__ import annotations
import math
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from flexagx.contracts import Sentinel

MAX_BODY_BYTES=21_000_000
MAX_ERRORS=12


def error_payload(code:str,reason:str,fallback:str='REJECT') -> dict:
    return {'error': Sentinel(kind=code,reason=reason[:160],fallback=fallback).model_dump()}


class LimitedBody:
    """ASGI preflight cap, including bodies sent without Content-Length."""
    def __init__(self, app, max_bytes=MAX_BODY_BYTES):
        self.app=app; self.max_bytes=max_bytes

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':
            await self.app(scope,receive,send)
            return
        headers=dict(scope.get('headers',[]))
        declared=headers.get(b'content-length',b'0')
        try: declared_bytes=int(declared)
        except (ValueError,OverflowError): declared_bytes=self.max_bytes+1
        if declared_bytes>self.max_bytes:
            await JSONResponse(error_payload('LIMIT_EXCEEDED','request body exceeds input budget'),status_code=413)(scope,receive,send)
            return
        received=0
        async def receive_bounded():
            nonlocal received
            packet=await receive()
            if packet['type']=='http.request':
                received+=len(packet.get('body',b''))
                if received>self.max_bytes: raise ValueError('request body exceeds input budget')
            return packet
        try:
            await self.app(scope,receive_bounded,send)
        except ValueError as exc:
            if str(exc)=='request body exceeds input budget':
                await JSONResponse(error_payload('LIMIT_EXCEEDED','request body exceeds input budget'),status_code=413)(scope,receive,send)
            else:
                raise


def install_guards(app):
    app.add_middleware(LimitedBody)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request:Request, exc:RequestValidationError):
        issues=exc.errors()[:MAX_ERRORS]
        labels=[]
        for issue in issues:
            loc='.'.join(str(x) for x in issue.get('loc',[])[:6])
            typ=str(issue.get('type','invalid'))[:40]
            labels.append(f'{loc}: {typ}')
        return JSONResponse(error_payload('INVALID','; '.join(labels)[:160] or 'invalid request'),status_code=422)

    @app.exception_handler(HTTPException)
    async def handled(request:Request,exc:HTTPException):
        code='NOT_FOUND' if exc.status_code==404 else ('LIMIT_EXCEEDED' if exc.status_code==413 else 'INVALID')
        return JSONResponse(error_payload(code,str(exc.detail)[:160] or 'request rejected'),status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def failed(request:Request,exc:Exception):
        return JSONResponse(error_payload('UNAVAILABLE','server rejected the operation safely'),status_code=500)
