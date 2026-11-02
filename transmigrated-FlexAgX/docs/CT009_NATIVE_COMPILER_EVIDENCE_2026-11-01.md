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

The log itself records only the *filename*, not the on-machine SHA-256. A subsequent operator-supplied Windows SHA-256 matches the repository candidate byte-for-byte (see source-identity synchronization below). This matching file digest does not independently attest the Windows path or the compile-session-to-file relationship.

## What has and has not been verified

- **Observed PASS:** ReShade compilation succeeded; shader warning count 0, including X4000 and X3571.
- **Observed PASS:** D3D12 device creation; ReShade 6.7.3.2150 runtime identification.
- **Previous source isolation:** exactly seven helper bodies differ from the CT-008 shader; CT-008 pow guard and shader pass structure preserved.
- **Not certified:** rendered pixel parity, colorimetry, first-frame state, resource synchronization, stability, other graphics APIs, performance, or production.
- **Not verified by this log:** independent Windows file-path/compile-session attestation or GPU tests. The operator-reported Windows file SHA-256 now matches the repository candidate.

## Next acceptance steps

1. **Completed as operator-reported:** Windows-side SHA-256 matches repository candidate. Independently verify Windows path and compile-to-file association if required.
2. Capture the same settled scene with CT-008 and CT-009, with matching effect settings, including a neutral gray, saturated gamut stress frame, zero-strength bypass, first-frame/reload sequence, and scene cut.
3. Keep raw logs and private captures outside the public repository. Store a reviewed, redacted summary only.
4. Leave the original upstream shader, CT-008 baseline and production branch unchanged until Operator approval.

**Native compiler warning criterion for this one configuration: met. GPU and production acceptance: open.**

## Source identity synchronization — November 1, 2026

The Operator supplied Windows SHA-256 `28B213958DAD8F264347B76192E6B685A61829D0B90778D6522A73301995163D` for the CT-009 candidate. SHA-256 recomputed from the staged repository candidate's 56,897 UTF-8 bytes is `28b213958dad8f264347b76192e6b685a61829d0b90778d6522a73301995163d`. **Comparison: exact match.** The repository Git blob SHA-1 (`12580cef4e2d9218cc019f8b78594b33bb03626b`) is a separate Git object identifier, not the source SHA-256.

**Scope:** This resolves the operator-reported Windows-to-repository *file-content* hash comparison. The Windows file path and relationship to the earlier compiler sessions are not independently attested by the logs. The zero-warning compile evidence remains valid as reported; GPU correctness, rendered parity, temporal behavior and production clearance remain **OPEN**. Production gate remains **LOCKED**.
