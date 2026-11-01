"""Single-owner, correctness-first, bounded orchestration glue.

Wire data stays validated by the v0.5 contracts. All temporal state commits occur
only after rendering and output validation succeed. No GPU parity is claimed.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any
from .adapters import ReferenceCPUAdapter, contracts, controller

FrameRequest = contracts.FrameRequest
FrameResult = contracts.FrameResult
FrameReceiptResult = contracts.FrameReceiptResult

class FrameConflict(Exception):
    pass

class FrameRejected(Exception):
    pass


def digest_request(request:FrameRequest)->str:
    raw=json.dumps(request.model_dump(mode='json'),sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


class CorrectnessFirstGlue:
    """Synchronous serial transaction coordinator, with injected numerical ports."""
    def __init__(self, store:Any, ports:Any):
        self.store=store
        self.ports=ports

    def frame(self, request:FrameRequest)->FrameResult:
        fingerprint=digest_request(request)
        try:
            previous=self.store.receipt(request.session_id,request.frame_index,fingerprint)
        except ValueError as exc:
            raise FrameConflict(str(exc)) from exc
        if previous.status=='REPLAY':
            if not isinstance(previous.response,FrameResult):
                raise FrameRejected('Invalid durable receipt; rejected')
            return previous.response
        # Validate and fully materialize the source image before mutating temporal state.
        try:
            pixels=self.ports.decode(request.image_png_base64)
        except (ValueError,OSError) as exc:
            raise FrameRejected('Invalid or unprocessable PNG') from exc
        height,width=int(pixels.shape[0]),int(pixels.shape[1])
        if request.settings.OverallStrength<=0 and request.settings.DebugView==0:
            response=FrameResult(
                image_png_base64=request.image_png_base64,width=width,height=height,
                session_id=request.session_id,frame_index=request.frame_index,mode='bypass')
            try:
                return self.store.record_bypass(request.session_id,request.frame_index,fingerprint,response)
            except ValueError as exc:
                raise FrameConflict(str(exc)) from exc
        try:
            observation=self.ports.observe(pixels,request.frame_index,request.settings)
            candidate=self.store.prepare(request.session_id,observation,request.settings,
                request.dt_ms,request.frame_index,fingerprint)
        except ValueError as exc:
            raise FrameConflict(str(exc)) from exc
        token=candidate.token
        try:
            control=candidate.control
            tone=self.ports.build(control,request.settings)
            if not tone.validation_passed:
                raise FrameRejected('Tone LUT did not pass validation')
            pixels_out=self.ports.render(pixels,request.settings,tone.lut,control.gain_ev)
            output=self.ports.encode(pixels_out)
            response=FrameResult(
                image_png_base64=output,width=width,height=height,
                session_id=request.session_id,frame_index=request.frame_index,
                observation=observation,control=control,
                tone_validation=tone.model_dump(exclude={'lut'}),mode='processed')
            committed=self.store.finalize(token,response)
            if not committed.committed:
                raise FrameConflict('State changed during processing; candidate not committed')
            return response
        except (ValueError,OverflowError,ArithmeticError) as exc:
            raise FrameRejected('Numerical validation failed; frame not committed') from exc
        finally:
            self.store.abort(token)
