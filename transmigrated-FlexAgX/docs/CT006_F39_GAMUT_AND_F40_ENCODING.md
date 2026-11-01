# CT-006 — F39 post-blend gamut containment, F40 explicit encoding hold

**Stage:** v0.6.0 development-only. **Operator acceptance required before promotion.**

## Original problem (F39)

In `FlexAgX_OutputPS`, the processed branch undergoes Oklab gamut roll-off,
then is mixed with the independently white-balanced original branch. Under
strong temperature adjustments that original branch may have channels < 0 or
> 1, and the **final mix is not guaranteed in gamut** even when the processed
branch is. The legacy `FA_Encode(clamp(finalLinear,...))` was then performing
component-wise hard clipping, which may distort the output hue.

## Candidate contract

- Preserve bit-for-bit the *pre-output* in-gamut composite values from the
  existing blend (strict three-channel 0..1 test). Do not rescale normally
  valid pixels and do not move white-balance earlier/later.
- Only when the **post-strength-mix** composite is outside [0,1], convert the
  signed linear RGB to Oklab, clamp L to [0,1], and search 12 times for the
  largest fractional chroma whose reconstructed RGB is strictly within gamut.
- Preserve hue direction by scaling *both* Oklab chroma components together,
  not clipping R, G, and B independently. Clamp final numerical outputs as a
  secondary safety constraint, not as the primary gamut mapping method.
- Preserve nine original candidate FX passes and all prior CT-001..CT-005
  corrections. Do not change gamma decoding, rendering, scene-cut dynamics,
  exposure weighting, Dithering or the UI slider range.

This is a **chosen bounded research-candidate containment strategy**, not a
claim that it matches the original author's intended color science, all
monitor profiles, or real ReShade GPU output. At L=0/1 the achievable gamut
may force zero chroma. The 12-step binary search is deliberately expensive;
correctness is prioritized over throughput. Float32 and backend-dependent
numeric divergences remain unmeasured.

## F40: explicit hold; no source behavior change

At `OverallStrength <= 0 && DebugView == 0`, `OutputPS` returns the exact
original **encoded** pixel without decoding, white balance, output conversion
or dithering. Any positive strength enters the selected `InputEncoding` /
`OutputEncoding` pipeline. If the two encodings differ, or temperature is not
neutral, or dithering is enabled, the limit as strength approaches zero need
**not** equal the exact zero-strength value. Both exact 0%-bypass and
continuity under all encoding combinations cannot be imposed at once without
changing the meaning of the slider or adding a new policy control.

For CT-006, exact 0% bypass **wins** and F40 is *characterized, not fixed*.
A future policy decision may introduce independently controlled output
conversion or encoded-domain strength blending; neither is implemented here.

## Verification and limitations

- `tests/test_color_contract_v06.py` tests in-gamut identity, out-of-gamut
  containment, hue direction, strict negative mutation and F40 transfers.
- `harness/color_oracle.py` supplies CPU mathematical witnesses; bounded
  seeded fuzz in `harness.suites gamut` exercises mixed branches and transfer
  discontinuities. 12-step source structure is checked by `source_audit`.
- Existing effect harness remains process-isolated and fail-closed. No actual
  ReShade FX compiler or GPU backend was invoked; no pixel equivalence,
  brightness fidelity or chromatic adaptation correctness is certified.
- F30/F31 input range and F18/F32 runtime initialization are still open.

**Release gate:** locked. `main` and the upstream shader remain unchanged.
