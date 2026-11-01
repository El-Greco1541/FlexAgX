"""Strict, bounded public contracts; never return JSON null for unavailable data."""
from __future__ import annotations
from typing import Literal
import math
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)

class HueRequest(StrictModel):
    stage: Literal['source-hue','curved-hue','output-gamut']
    a: float = Field(ge=-8.0, le=8.0)
    b: float = Field(ge=-8.0, le=8.0)

class HueResponse(StrictModel):
    status: Literal['OK','SENTINEL']
    angle_rad: float
    chroma: float
    guarded: bool
    reason: str

class HistogramRequest(StrictModel):
    bins: list[int] = Field(min_length=64, max_length=64)
    valid_count: int = Field(ge=0, le=2_000_000)
    white_count: int = Field(ge=0, le=2_000_000)
    sample_count: int = Field(ge=0, le=2_000_000)

    @model_validator(mode='after')
    def check_population(self):
        if any(type(v) is not int or v < 0 or v > 2_000_000 for v in self.bins):
            raise ValueError('invalid bin count')
        if sum(self.bins) != self.valid_count:
            raise ValueError('valid population must equal bin sum')
        if self.white_count > self.valid_count or self.valid_count > self.sample_count:
            raise ValueError('inconsistent population counters')
        return self

class HistogramResponse(StrictModel):
    status: Literal['OK']
    counters: list[int] = Field(min_length=67, max_length=67)
    cleared_first: bool

class TypedSentinel(StrictModel):
    kind: Literal['INVALID_INPUT','INTERNAL_FAILURE']
    reason: str
    fallback: Literal['NO_MUTATION']

class ErrorResponse(StrictModel):
    status: Literal['REJECTED']
    sentinel: TypedSentinel
