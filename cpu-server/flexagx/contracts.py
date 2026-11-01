"""Stable v1 wire contracts. Field spellings mirror original ReShade uniforms."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class WireModel(BaseModel):
    # All declared floats must be finite; undeclared structures are rejected.
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, validate_default=True)


class Sentinel(WireModel):
    kind: Literal['NOT_APPLICABLE','UNAVAILABLE','UNINITIALIZED','INVALID','NOT_FOUND','EXPIRED','CONFLICT','UPSTREAM_FAILURE','LIMIT_EXCEEDED']
    reason: str = Field(min_length=1,max_length=160)
    fallback: Literal['IDENTITY','REJECT','HOLD','RETRY_EXPLICIT','SKIP'] = 'REJECT'


class Settings(WireModel):
    OverallStrength: float = Field(100.0, ge=0, le=100)
    DebugView: int = Field(0, ge=0, le=2)
    AutoExposureStrength: float = Field(30.0, ge=0, le=100)
    ExposureOffset: float = Field(0.0, ge=-2, le=2)
    FreezeExposure: bool = False
    BrightenSpeed: float = Field(0.60, ge=.10, le=3)
    DarkenSpeed: float = Field(1.20, ge=.10, le=5)
    MaxChangeRate: float = Field(3.0, ge=.5, le=6)
    SceneChangeSensitivity: float = Field(.35, ge=.10, le=.60)
    Deadband: float = Field(.04, ge=0, le=.1)
    ClipGuard: float = Field(2.0, ge=.5, le=5)
    AutoHighlightKnee: bool = True
    HighlightKnee: float = Field(.5, ge=.4, le=.55)
    ShadowPreservation: float = Field(50.0, ge=0, le=100)
    HueRestoration: float = Field(100.0, ge=0, le=100)
    GamutRolloffStart: float = Field(.8, ge=.6, le=.95)
    ColorTemp: float = Field(6500, ge=2000, le=12000)
    LocalDetail: float = Field(20.0, ge=0, le=50)
    InputEncoding: Literal[0, 1] = 0
    OutputEncoding: Literal[0, 1] = 0
    Dithering: bool = True


class ImageRequest(WireModel):
    image_png_base64: str = Field(min_length=4, max_length=20_000_000)


class FrameRequest(ImageRequest):
    session_id: str = Field(default="default", pattern=r"^[A-Za-z0-9_-]{1,64}$")
    frame_index: int = Field(ge=0, le=2**63-1)
    dt_ms: float = Field(default=16.6667, ge=0, le=60_000)
    settings: Settings = Field(default_factory=Settings)


class ObserveRequest(ImageRequest):
    frame_index: int = Field(ge=0, le=2**63-1)
    settings: Settings = Field(default_factory=Settings)


class Observation(WireModel):
    histogram: list[int] = Field(min_length=64, max_length=64)
    @model_validator(mode='after')
    def check_population(self):
        if any(type(v) is not int or v<0 or v>2_000_000 for v in self.histogram):
            raise ValueError('histogram bins must be bounded nonnegative integers')
        if self.sample_count>2_000_000 or self.valid_count>self.sample_count or self.white_count>self.valid_count:
            raise ValueError('histogram counts violate sample population bounds')
        if sum(self.histogram)!=self.valid_count:
            raise ValueError('histogram count must equal valid_count')
        if not (-12.47394 <= self.e50 <= 4.02608 and -12.47394 <= self.e90 <= 4.02608):
            raise ValueError('percentile outside supported histogram domain')
        return self
    valid_count: int = Field(ge=0)
    white_count: int = Field(ge=0)
    sample_count: int = Field(ge=0)
    e50: float
    e90: float
    phase_x: Literal[0, 1]
    phase_y: Literal[0, 1]


class ControlRequest(WireModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    dt_ms: float = Field(ge=0, le=60_000)
    observation: Observation
    settings: Settings = Field(default_factory=Settings)
    frame_index: int = Field(default=0, ge=0, le=2**63-1)
    request_digest: str = Field(default="0"*64, min_length=64, max_length=64, pattern=r"^[a-f0-9]{64}$")


class ControlResult(WireModel):
    gain: float
    gain_ev: float
    knee: float
    auto_ev: float
    scene_key: float
    initialized: bool
    warmup: float
    scene_cut: bool
    valid_count: int


class ToneRequest(WireModel):
    gain: float = Field(ge=.25, le=4)
    knee: float = Field(ge=.4, le=.55)
    shadow_preservation: float = Field(ge=0, le=100)
    input_encoding: Literal[0, 1] = 0
    output_encoding: Literal[0, 1] = 0


def check_lut_values(values):
    if len(values) != 1024 or any(not (0.0 <= x <= 1.000001) for x in values):
        raise ValueError('LUT must have 1024 finite normalized entries')
    if any(values[i] + 1e-6 < values[i-1] for i in range(1, len(values))):
        raise ValueError('LUT must be monotone')
    return values


class ToneResult(WireModel):
    lut: list[float] = Field(min_length=1024, max_length=1024)
    @field_validator('lut')
    @classmethod
    def checked_lut(cls, values):
        return check_lut_values(values)
    validation_passed: bool
    used_fallback: bool
    attempts: int = Field(ge=1,le=4)
    final_knee: float = Field(ge=.4,le=.55)


class RenderRequest(ImageRequest):
    settings: Settings = Field(default_factory=Settings)
    gain_ev: float = Field(ge=-2, le=2)
    lut: list[float] = Field(min_length=1024, max_length=1024)
    @field_validator('lut')
    @classmethod
    def checked_render_lut(cls, values):
        return check_lut_values(values)



class RenderResult(WireModel):
    image_png_base64: str = Field(min_length=4,max_length=20_000_000)
    width: int = Field(ge=1,le=2_000_000)
    height: int = Field(ge=1,le=2_000_000)
    backend: str = "cpu-numpy-scipy"
    @model_validator(mode='after')
    def check_area(self):
        if self.width*self.height>2_000_000:
            raise ValueError('image area exceeds maximum')
        return self


class FrameResult(RenderResult):
    session_id: str
    frame_index: int
    observation: Observation | Sentinel = Field(default_factory=lambda: Sentinel(kind='NOT_APPLICABLE', reason='bypassed frame',fallback='IDENTITY'))
    control: ControlResult | Sentinel = Field(default_factory=lambda: Sentinel(kind='NOT_APPLICABLE', reason='bypassed frame',fallback='IDENTITY'))
    tone_validation: dict[str, bool | int | float] | Sentinel = Field(default_factory=lambda: Sentinel(kind='NOT_APPLICABLE', reason='bypassed frame',fallback='IDENTITY'))
    mode: Literal["bypass", "processed"]
    fidelity: str = "source-equation CPU approximation; not GPU/bit-exact"


class PrepareResult(WireModel):
    token: str = Field(min_length=32,max_length=64,pattern=r'^[a-f0-9]+$')
    control: ControlResult
    expires_in_seconds: int = Field(ge=1,le=30)


class TokenRequest(WireModel):
    token: str = Field(min_length=32,max_length=64,pattern=r'^[a-f0-9]+$')


class CommitResult(WireModel):
    committed: bool
    state: Literal['COMMITTED','ABORTED','EXPIRED','CONFLICT','NOT_FOUND']


class FrameReceiptQuery(WireModel):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    frame_index: int = Field(ge=0, le=2**63-1)
    request_digest: str = Field(min_length=64,max_length=64,pattern=r"^[a-f0-9]{64}$")


class FrameReceiptResult(WireModel):
    status: Literal['NEW','REPLAY']
    response: FrameResult | Sentinel = Field(default_factory=lambda: Sentinel(kind='NOT_APPLICABLE',reason='frame is not committed',fallback='RETRY_EXPLICIT'))


class FinalizeRequest(WireModel):
    token: str = Field(min_length=32,max_length=64,pattern=r'^[a-f0-9]+$')
    response: FrameResult


class FinalizeResult(WireModel):
    committed: bool
    state: Literal['COMMITTED','ALREADY_COMMITTED','CONFLICT','EXPIRED','NOT_FOUND']


class BypassRecordRequest(FrameReceiptQuery):
    response: FrameResult
