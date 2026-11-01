"""CT-005 S6 time+two-observation cut detection model. Not GPU execution."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class CutStep:
    fired: bool
    seconds: float
    update_reference: bool
    key_delta: float
    velocity: float


def cut_step(distance, sensitivity, elapsed, dt_ms, *, key=0., target=0., velocity=0., max_rate=3.):
    """Match corrected S6 transition. dt is clamped in the FX to [1ms, 250ms]."""
    values=(distance,sensitivity,elapsed,dt_ms,key,target,velocity,max_rate)
    if not all(math.isfinite(x) for x in values):raise ValueError('nonfinite input')
    if not (0<=distance<=1 and .1<=sensitivity<=.6 and 0<=elapsed<=1 and 0<=dt_ms<=100000 and
            -32<=key<=32 and -32<=target<=32 and -8<=velocity<=8 and .5<=max_rate<=6):
        raise ValueError('out-of-domain input')
    dt=min(.25,max(.001,dt_ms/1000.))
    had_candidate=elapsed>0
    if distance>sensitivity:
        duration=elapsed+dt
        update=False
    else:
        duration=0.
        update=True
    if had_candidate and duration>=.1:
        delta=max(-.5*max_rate,min(.5*max_rate,target-key))
        return CutStep(True,0.,True,delta,0.)
    return CutStep(False,duration,update,0.,velocity)


def old_cut_step(distance,sensitivity,elapsed,dt_ms,*,key=0.,target=0.,velocity=0.,max_rate=3.):
    """Pre-CT-005 difference witness; it could accept a one-frame cut."""
    new=cut_step(distance,sensitivity,elapsed,dt_ms,key=key,target=target,velocity=velocity,max_rate=max_rate)
    if distance>sensitivity and not elapsed and min(.25,max(.001,dt_ms/1000.))>=.1:
        delta=max(-.5*max_rate,min(.5*max_rate,target-key))
        return CutStep(True,0.,True,delta,0.)
    return new


def auto_strength_zero_contract(exposure_offset, prior_auto_ev, tracker_advanced):
    """F36 regression witness for the unchanged 0%-auto API contract only."""
    if not all(map(math.isfinite,(exposure_offset,prior_auto_ev))):raise ValueError('nonfinite')
    if not (-2<=exposure_offset<=2):raise ValueError('manual offset bounds')
    # AutoExposureStrength <= 0 explicitly forces auto applied EV to zero.
    return {'applied_auto_ev':0.,'total_gain_ev':exposure_offset,'tracker_advanced':bool(tracker_advanced)}
