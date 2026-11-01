# CT-005 / F29 — Scene-cut candidate must span two observations

**Status:** correction-first research candidate, not deployed; production gate LOCKED.

## Reproduced defect

The v0.4 S6 controller advanced `cutCount += dt` and accepted a scene cut as soon as `cutCount >= 0.10` seconds. With the existing `frametime` clamp to 250 ms, an initial discrepant histogram arriving after 100–250 ms could trigger confirmation immediately. That violates the source comment and intended control behavior that a one-frame difference must not reset exposure.

## Minimal correction

Capture `bool hadCutCandidate = (cutCount > 0.0)` **before** adding the current frame's dt. Confirm only if that flag is true **and** the accumulated timer reaches `_FA_SCENE_CUT_SECONDS`. This requires two consecutive discrepant observations, while retaining the prior 0.10 s threshold, difference metric, baseline-hold, key-jump bound, applied-auto-exposure EV rate clamp, cold-start reset and timer cancellation.

No new texture, storage format, pass or thread is introduced. The only candidate shader change relative to v0.4 is the S6 decision condition and its explanation.

## Numerical contract and boundary

- Single discrepant frame: holds old histogram reference and begins timer, even with `dt = 250ms`.
- Second discrepant frame: confirms only if accumulated timer >= 100ms; resets cutCount and accepts new baseline.
- A stable/interrupted frame at or below the sensitivity threshold: cancels the timer and accepts current baseline.
- With an already positive timer, all existing v0.4 decisions and key correction bounds are unchanged.
- The internal key correction remains dt-independent at confirmation (`±0.5 * MaxChangeRate`), while applied auto exposure is separately frame-rate limited. This is a retained behavior, not an assertion of full temporal equivalence.
- **F36 policy unchanged:** `AutoExposureStrength=0` forces zero automatic exposure contribution and preserves manual ExposureOffset; internal tracking may continue. FreezeExposure is a separate control. Any alteration to internal tracking needs an Operator-selected behavior contract.

## Evidence and exclusions

Independent legacy/candidate oracles, strict-threshold checks, 4,000 random prior-candidate equivalence fixtures, deliberately mutated shader assertions and 1,000-/2,000-frame harness campaigns. Original SHA-256 pinned; nine passes unchanged. 100/100 pytest and 16/16 harness self-tests. Two isolated campaigns passed 52,986 and 54,014 checks. See `VERIFICATION_REPORT.json` for the per-phase, per-seed evidence.

**Not demonstrated:** real FX compiler acceptance, GPU state persistence, GPU barrier behavior, pixel fidelity, or actual ReShade frame-time/scene behavior. Candidate acceptance requires real-runtime tests at normal and stalled FPS, intermittent scene differences, 0%-strength, freeze, reload and repeated scene cuts.
