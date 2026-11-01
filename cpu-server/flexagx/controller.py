"""Reference-style exposure state machine with per-session in-memory isolation.

State is NOT persisted across process restart. Initialization is deterministic in
this CPU port; the shader's original GPU-resource first-use contract is unresolved.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import threading
import copy
import time
import uuid
import os
from .journal import Journal
from .contracts import FrameReceiptResult, FrameResult, FinalizeResult, Sentinel
import numpy as np
from .contracts import Observation, Settings, ControlResult, PrepareResult, CommitResult, Sentinel
from .compute import GREY, LOG_MIN, dn


def scalar_clamp(x, a, b): return min(max(x,a),b)


def grey_ev():
    lo=-14.; hi=6.
    for _ in range(30):
        mid=.5*(lo+hi)
        if float(dn(2**mid))<GREY: lo=mid
        else: hi=mid
    return (lo+hi)*.5


GREY_EV=grey_ev()


@dataclass
class State:
    x: float = 0.0
    v: float = 0.0
    knee: float = 0.0
    cut_count: float = 0.0
    stored_lambda: float = 0.0
    initialized: bool = False
    applied_auto_ev: float = 0.0
    warmup: float = 0.0
    prev_hist: list[float] = field(default_factory=lambda: [0.0]*64)
    frames: int = 0
    lifecycle: str = "UNINITIALIZED"

    def summary(self):
        return {"scene_key":self.x, "velocity":self.v,"knee":self.knee,"cut_count":self.cut_count,
                "stored_lambda":self.stored_lambda,"initialized":self.initialized,
                "applied_auto_ev":self.applied_auto_ev,"warmup":self.warmup,"frames":self.frames,
                "hist_reference_sum":sum(self.prev_hist),"lifecycle":self.lifecycle}


def step(state:State,obs:Observation,settings:Settings,dt_ms:float)->ControlResult:
    if state.frames>=2**63-1:
        raise ValueError('session frame counter limit reached; reset session')
    dt=scalar_clamp(dt_ms/1000.0,.001,.25)
    T=obs.valid_count; e50=obs.e50; e90=obs.e90
    dark_gate=scalar_clamp((e50+9)/3,0,1) if T>=64 else 0.
    adapt=(not settings.FreezeExposure) and dark_gate>0
    if settings.AutoExposureStrength<=0 or (not settings.FreezeExposure and dark_gate<=0):
        state.stored_lambda=0.0
    confirmed_cut=False
    update_ref=True
    if adapt:
        raw_knee=scalar_clamp(2**e90,.4,.55) if settings.AutoHighlightKnee else settings.HighlightKnee
        if not state.initialized:
            state.x=e50; state.v=0; state.knee=raw_knee
            state.initialized=True; state.warmup=0
        target=e50
        if abs(target-state.x)<settings.Deadband: target=state.x
        tau=settings.BrightenSpeed if target>state.x else settings.DarkenSpeed
        w=1/max(tau,2*dt)
        accel=w*w*(target-state.x)-2*w*state.v
        state.v=scalar_clamp(state.v+accel*dt,-settings.MaxChangeRate,settings.MaxChangeRate)
        state.x+=state.v*dt
        # The original shader does not guard T here; adapt guarantees T >= 64.
        delta=.5*sum(abs((float(c)/T)-p) for c,p in zip(obs.histogram,state.prev_hist))
        if delta>settings.SceneChangeSensitivity:
            state.cut_count+=dt
            update_ref=False
        else:
            state.cut_count=0.0
        if state.cut_count>=.10:
            state.x+=scalar_clamp(e50-state.x,-.5*settings.MaxChangeRate,.5*settings.MaxChangeRate)
            state.v=0.0
            state.cut_count=0.0
            confirmed_cut=True
            update_ref=True
        state.knee+=(1-np.exp(-dt/.6))*(raw_knee-state.knee)
        state.lifecycle='ACTIVE'
        state.warmup=min(state.warmup+dt,1.0)
        white_fraction=obs.white_count/obs.sample_count if obs.sample_count else 0.0
        f=scalar_clamp(1-white_fraction/max(settings.ClipGuard/100,1e-6),0,1)
        state.stored_lambda=(settings.AutoExposureStrength/100)*f*dark_gate*scalar_clamp(state.warmup/.5,0,1)
    else:
        state.cut_count=0.0
        update_ref=True
        state.lifecycle='HOLD' if state.initialized else 'UNINITIALIZED'
    target_auto_ev=scalar_clamp(state.stored_lambda*(GREY_EV-state.x),-2,2)
    if settings.AutoExposureStrength<=0: state.applied_auto_ev=0.0
    elif not settings.FreezeExposure:
        step_ev=settings.MaxChangeRate*dt
        state.applied_auto_ev+=scalar_clamp(target_auto_ev-state.applied_auto_ev,-step_ev,step_ev)
    gain_ev=scalar_clamp(state.applied_auto_ev+settings.ExposureOffset,-2,2)
    build_knee=scalar_clamp(state.knee,.4,.55) if settings.AutoHighlightKnee else settings.HighlightKnee
    if update_ref:
        state.prev_hist=[float(c)/T if T else 0.0 for c in obs.histogram]
    state.x=scalar_clamp(state.x,LOG_MIN-3.0,4.026069+3.0)
    state.v=scalar_clamp(state.v,-settings.MaxChangeRate,settings.MaxChangeRate)
    state.frames+=1
    return ControlResult(gain=2**gain_ev,gain_ev=gain_ev,knee=build_knee,
                         auto_ev=state.applied_auto_ev,scene_key=state.x,initialized=state.initialized,
                         warmup=state.warmup,scene_cut=confirmed_cut,valid_count=T)


class SessionStore:
    def __init__(self,max_sessions=128,db_path=None):
        self._journal=Journal(db_path if db_path is not None else os.getenv("FLEXAGX_STATE_DB",":memory:"))
        self._states:dict[str,State]={sid:State(**raw) for sid,(raw,idx) in self._journal.load().items()}
        self._lock=threading.RLock()
        self.max_sessions=max_sessions
        if len(self._states)>max_sessions: raise ValueError("persisted session population exceeds configured bound")
        self._pending: dict[str, tuple[str,int,State,float]] = {}
        self._max_pending=128
        self._pending_seconds=30.0
        self._pending_identity: dict[str,tuple[str,int,str]]={}

    def step(self,session_id,obs,settings,dt_ms):
        with self._lock:
            if session_id not in self._states:
                if len(self._states)>=self.max_sessions:
                    raise ValueError('Session capacity reached; reset an existing session')
                self._states[session_id]=State()
            return step(self._states[session_id],obs,settings,dt_ms)

    def get(self,session_id):
        with self._lock:
            return (self._states[session_id].summary() if session_id in self._states and self._states[session_id].frames>0
                    else Sentinel(kind='NOT_FOUND',reason='session does not exist',fallback='REJECT').model_dump())

    def reset(self,session_id):
        with self._lock:
            removed=session_id in self._states
            if removed: del self._states[session_id]
            for token, (owner, _, _, _) in list(self._pending.items()):
                if owner==session_id:
                    del self._pending[token]
                    self._pending_identity.pop(token,None)
            self._journal.reset(session_id)
            return removed

    def _expire(self):
        now=time.monotonic()
        for token, (owner, base, candidate, expiry) in list(self._pending.items()):
            if now>=expiry:
                del self._pending[token]
                self._pending_identity.pop(token,None)

    def receipt(self,session_id,frame_index,request_digest):
        with self._lock:
            found=self._journal.find(session_id,frame_index)
            if found:
                if found[0]!=request_digest: raise ValueError('frame index already committed with different request')
                return FrameReceiptResult(status='REPLAY',response=FrameResult.model_validate_json(found[1]))
            if frame_index<=self._journal.last(session_id):
                raise ValueError('stale or evicted frame: cannot safely replay')
            if any(identity[0]==session_id and identity[1]==frame_index for identity in self._pending_identity.values()):
                raise ValueError('frame index currently pending')
            return FrameReceiptResult(status='NEW')

    def record_bypass(self,session_id,frame_index,request_digest,response):
        """Journal bypass output without incrementing temporal frames."""
        with self._lock:
            self._expire()
            found=self.receipt(session_id,frame_index,request_digest)
            if found.status=='REPLAY': return found.response
            if any(identity[0]==session_id for identity in self._pending_identity.values()):
                raise ValueError('session has a pending frame')
            if session_id not in self._states and len(self._states)>=self.max_sessions:
                raise ValueError("session capacity exceeded")
            candidate=self._states[session_id] if session_id in self._states else State()
            self._journal.write(session_id,frame_index,request_digest,response.model_dump(mode='json'),uuid.uuid4().hex,candidate.__dict__)
            self._states[session_id]=candidate
            return response

    def finalize(self,token,response):
        with self._lock:
            self._expire()
            found_token=self._journal.conn.execute('SELECT session_id,frame_index,digest,response_json FROM receipts WHERE token=?',(token,)).fetchone()
            if found_token:
                stored=FrameResult.model_validate_json(found_token[3])
                if stored.model_dump()==response.model_dump():
                    return FinalizeResult(committed=True,state='ALREADY_COMMITTED')
                raise ValueError('same token with mismatched response')
            pending=self._pending.get(token)
            if not pending: return FinalizeResult(committed=False,state='EXPIRED')
            owner,base,candidate,expiry=pending
            identity=self._pending_identity.get(token)
            if identity is None: return FinalizeResult(committed=False,state='CONFLICT')
            sid,index,digest=identity
            if sid!=owner or response.session_id!=sid or response.frame_index!=index:
                raise ValueError('finalize identity mismatch')
            current=self._states[owner].frames if owner in self._states else -1
            if current!=base: return FinalizeResult(committed=False,state='CONFLICT')
            if owner not in self._states and len(self._states)>=self.max_sessions:
                return FinalizeResult(committed=False,state='CONFLICT')
            self._journal.write(sid,index,digest,response.model_dump(mode='json'),token,candidate.__dict__)
            self._states[sid]=candidate
            self._pending.pop(token,None);self._pending_identity.pop(token,None)
            return FinalizeResult(committed=True,state='COMMITTED')

    def prepare(self,session_id,obs,settings,dt_ms,frame_index=0,request_digest='0'*64):
        with self._lock:
            self._expire()
            check=self.receipt(session_id,frame_index,request_digest)
            if check.status=="REPLAY": raise ValueError("already committed: use receipt")
            if any(owner==session_id for owner, _, _, _ in self._pending.values()):
                raise ValueError('session already has a pending frame')
            if len(self._pending)>=self._max_pending:
                raise ValueError('pending-frame capacity exceeded')
            if session_id not in self._states and len(self._states)>=self.max_sessions:
                raise ValueError('session capacity exceeded')
            state=copy.deepcopy(self._states[session_id]) if session_id in self._states else State()
            base=self._states[session_id].frames if session_id in self._states else -1
            result=step(state,obs,settings,dt_ms)
            token=uuid.uuid4().hex
            self._pending[token]=(session_id,base,state,time.monotonic()+self._pending_seconds)
            self._pending_identity[token]=(session_id,frame_index,request_digest)
            return PrepareResult(token=token,control=result,expires_in_seconds=30)

    def commit(self,token):
        with self._lock:
            self._expire()
            if token not in self._pending:
                return CommitResult(committed=False,state='EXPIRED')
            owner,base,candidate,expiry=self._pending.pop(token)
            self._pending_identity.pop(token,None)
            current=self._states[owner].frames if owner in self._states else -1
            if current!=base:
                return CommitResult(committed=False,state='CONFLICT')
            if owner not in self._states and len(self._states)>=self.max_sessions:
                return CommitResult(committed=False,state='CONFLICT')
            self._states[owner]=candidate
            return CommitResult(committed=True,state='COMMITTED')

    def abort(self,token):
        with self._lock:
            self._expire()
            if token in self._pending:
                del self._pending[token]
                self._pending_identity.pop(token,None)
                return CommitResult(committed=False,state='ABORTED')
            return CommitResult(committed=False,state='NOT_FOUND')
