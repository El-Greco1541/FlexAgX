"""Source-focused key adaptation oracle. Not GPU or complete shader verification."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class KeyState:
    key: float
    velocity: float
    settled: bool


def step_key(key, velocity, target, dt_ms, deadband=.04, brighten_speed=.6,
             darken_speed=1.2, max_change_rate=3.):
    if not all(map(math.isfinite, (key,velocity,target,dt_ms,deadband,brighten_speed,darken_speed,max_change_rate))):
        raise ValueError('nonfinite adaptation input')
    if not (-32 <= key <= 32 and -32 <= target <= 32 and -8 <= velocity <= 8 and
            0 <= deadband <= .1 and .1 <= brighten_speed <= 3 and
            .1 <= darken_speed <= 5 and .5 <= max_change_rate <= 6 and 0 <= dt_ms <= 100000):
        raise ValueError('out-of-domain adaptation input')
    dt = min(.25, max(.001, dt_ms / 1000))
    if abs(target-key) <= deadband:
        return KeyState(key, 0., True)
    tau=brighten_speed if target>key else darken_speed
    w=1. / max(tau, 2*dt)
    acceleration=w*w*(target-key)-2*w*velocity
    next_v=min(max_change_rate,max(-max_change_rate,velocity+acceleration*dt))
    return KeyState(key+next_v*dt, next_v, False)


def legacy_key_step(key, velocity, target, dt_ms, deadband=.04,
                    brighten_speed=.6,darken_speed=1.2,max_change_rate=3.):
    """Exact pre-CT-004 CPU equation for regression comparisons only."""
    dt=min(.25,max(.001,dt_ms/1000))
    if abs(target-key)<deadband:target=key
    tau=brighten_speed if target>key else darken_speed
    w=1./max(tau,2*dt)
    v=min(max_change_rate,max(-max_change_rate,velocity+(w*w*(target-key)-2*w*velocity)*dt))
    return KeyState(key+v*dt,v,False)


def scene_cut_probe(distance, sensitivity, cut_seconds, dt_ms, threshold_seconds=.1):
    """Diagnostic S6 timer: preserves existing shader behavior; no policy change."""
    dt=min(.25,max(.001,dt_ms/1000))
    if distance>sensitivity:
        seconds=cut_seconds+dt
        return (seconds>=threshold_seconds, 0. if seconds>=threshold_seconds else seconds,seconds>=threshold_seconds)
    return (False,0.,False)
