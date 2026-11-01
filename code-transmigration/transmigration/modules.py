"""Immutable, ordered, independently inspectable stage-to-service mapping.

This map does NOT assert that the CPU backend has independent GPU render targets.
"""
from dataclasses import dataclass
from typing import Literal

StageStatus = Literal['source_equation_approximation', 'grouped_cpu_approximation']

@dataclass(frozen=True)
class Stage:
    order: int
    source_pass: str
    shader_entry: str
    owner: Literal['observer','controller','tone','renderer']
    adapter: str
    status: StageStatus

STAGES: tuple[Stage,...] = (
    Stage(1,'FlexAgX_HistogramPass','FlexAgX_Histogram','observer','observe','source_equation_approximation'),
    Stage(2,'FlexAgX_StatePass','FlexAgX_State','controller','step_and_make_lut','grouped_cpu_approximation'),
    Stage(3,'FlexAgX_CurvePass','FlexAgX_CurvePS','renderer','render_pixels','grouped_cpu_approximation'),
    Stage(4,'FlexAgX_HuePass','FlexAgX_HuePS','renderer','render_pixels','grouped_cpu_approximation'),
    Stage(5,'FlexAgX_DetailMeanPass','FlexAgX_DetailMeanPS','renderer','render_pixels','grouped_cpu_approximation'),
    Stage(6,'FlexAgX_DetailBasePass','FlexAgX_DetailBasePS','renderer','render_pixels','grouped_cpu_approximation'),
    Stage(7,'FlexAgX_DetailApplyPass','FlexAgX_DetailApplyPS','renderer','render_pixels','grouped_cpu_approximation'),
    Stage(8,'FlexAgX_OutputPass','FlexAgX_OutputPS','renderer','render_pixels','grouped_cpu_approximation'),
)

SERVICE_NAMES=('observer','controller','tone','renderer','glue')
