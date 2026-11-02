# CT-009 — Native ReShade compilation evidence (2026-11-01)

**Disposition:** CT-009 compiled with **zero shader compiler warnings**, on the observed D3D12 host. Research evidence only. **Production gate: LOCKED.**

## Scope and provenance

- Evidence supplied by the Operator as a ReShade session log.
- ReShade version: `6.7.3.2150` (64-bit).
- Host rendering API: D3D12 (D3D12 device creation logged).
- Reported shader file: `FlexAgX_transmigrated_CT009_X4000_candidate.fx`.
- First full-success line: 20:52:15.436; 1.774 seconds, INFO (no "with warnings").
- Second success line: 20:53:00.236; 0.019 seconds, INFO (fast repeat, not the sole acceptance evidence).
- No X4000, X3571, or other shader compiler-warning diagnostic was found anywhere in the supplied log; no shader compilation errors were found.
- The log contains **six non-compiler WARN** messages about ignored LoadLibrary calls. These are separate runtime notices, not shader warnings; do not describe the whole ReShade log as warning-free.
- Raw log SHA-256: `27ca6f59511ca3398ddb8ad39f378a6525e9b1e32481c72318069ce04d82cdf8`; raw content remains local and is **not** committed.
- Comparison reference: CT-008 warning-bearing full compiler report (X4000 ×19, X3571 ×0). CT-009's filename and zero compiler diagnostics are stronger evidence than fast-cache INFO-only compilation, but a controlled A/B build with hash-bound source is still desirable.

## Shader source identity

The staged experimental candidate is preserved at
`shader/FlexAgX_transmigrated_CT009_X4000_candidate.fx`, Git blob
`12580cef4e2d9218cc019f8b78594b33bb03626b` (blob object SHA, **not** a Windows source SHA-256).

The uploaded session log records only the *filename*; it does **not** independently contain the shader's on-machine SHA-256. Therefore the local compiled FX bytes have not been cryptographically bound to the staged Git blob. Record the file's SHA-256 on the Windows host before closing the provenance requirement.

## What has and has not been verified

- **Observed PASS:** ReShade compilation succeeded; shader warning count 0, including X4000 and X3571.
- **Observed PASS:** D3D12 device creation; ReShade 6.7.3.2150 runtime identification.
- **Previous source isolation:** exactly seven helper bodies differ from the CT-008 shader; CT-008 pow guard and shader pass structure preserved.
- **Not certified:** rendered pixel parity, colorimetry, first-frame state, resource synchronization, stability, other graphics APIs, performance, or production.
- **Not verified by this log:** binary/file identity on the Windows host; independently reproduced GPU tests.

## Next acceptance steps

1. Record SHA-256 of the actual Windows-side CT-009 shader and compare it against the candidate bytes from this branch.
2. Capture the same settled scene with CT-008 and CT-009, with matching effect settings, including a neutral gray, saturated gamut stress frame, zero-strength bypass, first-frame/reload sequence, and scene cut.
3. Keep raw logs and private captures outside the public repository. Store a reviewed, redacted summary only.
4. Leave the original upstream shader, CT-008 baseline and production branch unchanged until Operator approval.

**Native compiler warning criterion for this one configuration: met. GPU and production acceptance: open.**
