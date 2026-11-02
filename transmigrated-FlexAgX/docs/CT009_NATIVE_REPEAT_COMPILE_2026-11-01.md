# CT-009 — Independent repeat compile log addendum (2026-11-01)

**Status:** Warning-remediation criterion replicated in an additional operator-supplied ReShade log. Research-stage documentation only; production gate LOCKED.

## Fresh native evidence

- Source: new operator-provided log fragment, 1,514 physical lines. Raw log stays outside GitHub.
- Raw log SHA-256: `af5b4a293c507bb54e220d7c89e4a24994bec5ee2c72cf43e3ed8652ce70e5d8`.
- Candidate filename: `FlexAgX_transmigrated_CT009_X4000_candidate.fx`.
- Candidate success entries: **six**; all tagged `INFO | Successfully compiled`, none tagged `WARN`.
- Substantial compilation at **20:54:34.416**, duration **3.043 s**; no warning stanza.
- Subsequent rapid successes: 20:55:47.192 (0.017 s), 20:56:28.346 (0.016 s), 20:56:54.284 (0.018 s), 20:57:22.143 (0.017 s), 20:58:03.640 (0.016 s).
- **FlexAgX compiler diagnostics:** X4000 = 0; X3571 = 0; compilation errors = 0.
- **Whole-log diagnostics, not attributed to FlexAgX:** 948 X4000 warning lines under 61 warning-bearing compilations of *other* shaders. 472 successful compilation entries across the excerpt. Global warnings must NOT be presented as FlexAgX warnings.

## Interpretation and limits

This is a second recorded multi-second, warning-free compilation of the CT-009-named effect following the previous **1.774-second, warning-free** run. The later 0.016–0.018-second entries may be cached and are not five independent full compiler validations. It is not a GPU image-quality or equivalence test.

The uploaded fragment **does not repeat** the ReShade version, renderer API, GPU, driver or program initialization lines. The separate prior CT-009 session log identified ReShade 6.7.3.2150 and D3D12; this new fragment alone cannot independently confirm those attributes. It also records a *filename*, not a Windows shader SHA-256.

Git candidate: `shader/FlexAgX_transmigrated_CT009_X4000_candidate.fx`. Preserve the CT-008 baseline, original upstream reference and correction history unchanged.

## Remaining verification gates

1. On Windows, capture `Get-FileHash -Algorithm SHA256` for the exact compiled CT-009 `.fx` file and compare with the expected Git candidate digest.
2. Verify correct rendering, 0%-strength bypass, neutral/grayscale, saturated gamut limits, scene-cut timing, first-frame and reload across matched CT-008/CT-009 captures.
3. Do not treat this log as proof of numerical/GPU parity, warnings elsewhere resolved, other backend compatibility, or release authorization.

**Conclusion:** CT-009 X4000/X3571 compiler-warning objective is **confirmed in the supplied native log observations**, while source-hash binding, GPU fidelity and production acceptance remain open.
