# CT-009 — X4000 single-exit source trial

**State:** staged, NOT native compiled, production LOCKED. This is an experimental warning-remediation candidate, not a proved fix.

**Baseline:** CT-008 shader from commit `4c5752c91a9d0d0c8100aa6bc250ae7ed0602b34`. The baseline shader file and upstream reference are unchanged on this branch.

**Trial:** `shader/FlexAgX_transmigrated_CT009_X4000_candidate.fx` is a parallel file. Changes are confined to seven helpers, each with an explicitly initialized single-exit result: `FA_Decode`, `FA_Encode`, `FA_Dn`, `FA_Native`, `FA_ComposedCurve`, `FA_WhiteBalance`, `FA_ConstrainGamutAfterMix`. A structural source-mask comparison confirmed no edits outside these bodies.

## Evidence before the trial

The operator's November 1 ReShade log reports a 3.605-second successful CT-008 compilation with **X4000 ×19**, **X3571 ×0**. The X4000 distribution was Decode 5, Dn 5, Native 4, Encode 2, ComposedCurve 1, WhiteBalance 1, ConstrainGamutAfterMix 1. Other shaders in the log also emit X4000. Fast INFO-only entries are not reliable evidence of a full warning-free recompile.

Generated HLSL identifiers `F__FA_*` do not establish the underlying source variable or the absence of a real initialization problem. The single-exit transformation is a compiler-dataflow hypothesis. It does not change GPU resource ordering, groupshared state, pass order, or the CT-008 pow guard.

## Verification

- **PASS:** seven-function source-change isolation; non-target bytes intact.
- **PASS:** independent CPU branch-shape mathematical check: 5,000 seeded AgX curve combinations plus scalar boundary cases. These check a mathematical model, not ReShade execution.
- **NOT RUN:** CT-009 native compiler, GPU pixels, HDR, performance, or visual parity.
- **NOT ESTABLISHED:** X4000 warnings removed.

## Native A/B procedure

1. On the same host/backend, retain CT-008 as a known baseline. Copy **only** the CT-009 trial shader into the ReShade search path; identify it by its distinct filename.
2. Record SHA-256 using PowerShell `Get-FileHash -Algorithm SHA256 '<full candidate path>'`. Record ReShade version, backend, device and driver privately.
3. Force a genuine full effect compile/reload. Record the **CT-009 filename**, actual success/failure, X4000 and X3571 counts and helper names, not the aggregate warnings from other effects. Keep raw logs/private paths out of public GitHub.
4. Compare the result with CT-008's **19 X4000 / 0 X3571**. INFO-only cached builds do not prove warning elimination.
5. Check matched CT-008 vs CT-009 captures, first frame/reload, exact zero-strength bypass, scene changes, neutral ColorTemp, and gamut boundary colors.

**Pass criterion:** matched-backend full compile gives fewer than 19 X4000 warnings with digest-bound source identity and no new errors. **Complete warning correction:** zero X4000 and zero X3571, then independently review pixel/state behavior. A count of 19 means this trial failed to reduce warnings. Do not suppress warnings or claim GPU certification.

**No merge, release, or promotion without explicit Operator authorization.**
