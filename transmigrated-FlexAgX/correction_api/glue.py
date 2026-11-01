"""Explicit replaceable computation ports; no hidden state or scheduling."""
from dataclasses import dataclass
from typing import Callable
from .models import HueRequest, HueResponse, HistogramRequest, HistogramResponse
from .modules import safe_hue, clear_and_accumulate

@dataclass(frozen=True)
class CorrectionPorts:
    hue: Callable[[HueRequest], HueResponse] = safe_hue
    histogram: Callable[[HistogramRequest], HistogramResponse] = clear_and_accumulate

@dataclass(frozen=True)
class CorrectionCoordinator:
    ports: CorrectionPorts

    def hue(self, request: HueRequest) -> HueResponse:
        return self.ports.hue(request)

    def histogram(self, request: HistogramRequest) -> HistogramResponse:
        return self.ports.histogram(request)
