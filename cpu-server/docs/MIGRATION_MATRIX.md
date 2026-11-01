# Migration matrix — original FX → service component

| Original resource or pass | Python port | Microserver | Fidelity / difference |
|---|---|---|---|
| `FA_BackBuffer` | `png_decode` | gateway/observer/renderer | RGBA8 PNG, not arbitrary GPU framebuffer |
| P1 `FlexAgX_Histogram` | `compute.observe` | observer | Same global 2×2 phase/counters; CPU float64 |
| P2 `FlexAgX_State` | `controller.step` | controller | Same state update/order; **deterministic zero initialization** (original runtime unverified) |
| P2 `FA_ComposedCurve`/validation | `compute.make_lut` | tone | Same 1024-point domain, retry/fallback; CPU scalar/quantization |
| P3 `FlexAgX_CurvePS` | `compute.curve_rgb` | renderer | Inset, LUT, outset in float64; A buffer half cast |
| P4 `FlexAgX_HuePS` | `compute.hue_restore` | renderer | Oklab hue logic; B buffer half cast |
| P5 `FlexAgX_DetailMeanPS` | `compute.detail` first filtering stage | renderer | 5×5 clamped border with scipy; RG16F cast |
| P6 `FlexAgX_DetailBasePS` | `compute.detail` second filtering stage | renderer | 5×5 clamped border, RG16F cast; texture sampler interpolation not exact |
| P7 `FlexAgX_DetailApplyPS` | `compute.detail` ratio | renderer | ratio bounded 0.25–4; D buffer half cast |
| P8 `FlexAgX_OutputPS` | `compute.render_pixels` | renderer | LMS white balance, Oklab gamut bisection, strength blend, debug, encoding and dithering |
| FX technique scheduling | `services.gateway.api_frame` | gateway | HTTP sequential orchestration; no GPU execution |
| `frametime`, `framecount` | `dt_ms`, `frame_index` | gateway | Caller supplies frame clock; no engine-sourced timing |
| FX resource persistence | `SessionStore` | controller | Per-session RAM; no GPU texture resource fidelity |

## Not migrated

No actual ReShade runtime add-on, Vulkan/D3D/OpenGL execution, shader compiler, HDR pixel encoding, GPU buffers, GPU profiling, GPU-driven frame capture, D3D11/12 textures, Vulkan image handles, hardware synchronization or production-grade transport. The original `.fx` is preserved instead of rewritten.

## Findings

The existing static audit and source research through F43 remain open. Known source semantics are reproduced where possible, **not silently corrected**. F19 compilation is unresolved. GPU-domain `atan2(0,0)` handling is not emulated (NumPy provides a determinate result at the origin). See F01–F43 CSV.
