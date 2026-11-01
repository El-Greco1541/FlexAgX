"""Pure bounded correction probes, separated from HTTP and FX runtime."""
from __future__ import annotations
import math
from .models import HueRequest, HueResponse, HistogramRequest, HistogramResponse

_THRESHOLDS = {'source-hue': 1.0e-4, 'curved-hue': 1.0e-6, 'output-gamut': 1.0e-6}

def safe_hue(req: HueRequest) -> HueResponse:
    a, b = req.a, req.b
    # Validation occurs at input boundary; do not compute an undefined angle.
    if not (math.isfinite(a) and math.isfinite(b)):
        raise ValueError('nonfinite component')
    chroma = math.hypot(a, b)
    if (chroma < _THRESHOLDS[req.stage] if req.stage == 'source-hue' else chroma <= _THRESHOLDS[req.stage]):
        return HueResponse(status='SENTINEL', angle_rad=0.0, chroma=chroma,
                           guarded=True, reason='ACHROMATIC_FALLBACK')
    return HueResponse(status='OK', angle_rad=math.atan2(b, a), chroma=chroma,
                       guarded=False, reason='DEFINED_ANGLE')

def clear_and_accumulate(req: HistogramRequest) -> HistogramResponse:
    # Precisely 67 slots are zeroed prior to each bounded 64-bin accumulation.
    counters = [0 for _ in range(67)]
    for index in range(64):
        counters[index] += req.bins[index]
    counters[64] = req.valid_count
    counters[65] = req.white_count
    counters[66] = req.sample_count
    return HistogramResponse(status='OK', counters=counters, cleared_first=True)
