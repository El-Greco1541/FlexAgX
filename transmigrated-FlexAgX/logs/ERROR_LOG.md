# Error / limitations register
| ID | State | Description |
|---|---|---|
| CT-E01 | Controlled | Hue `atan2` origin now guarded in source; GPU acceptance untested |
| CT-E02 | Controlled | Histogram preclear pass before P1 accumulation; GPU memory scheduling untested |
| CT-E03 | Open | FA_State and FA_HistPrev first-use are not proved initialized |
| CT-E04 | Open | No ReShade FX compiler/driver tests; no GPU parity |
| CT-E05 | Open | F39/F40 policy and perceptual correctness remain unresolved |
| CT-E06 | Explicit | API exposes correction probes only, not full image rendering or ReShade control |

## Harness v0.2.0 observations
- H02-01: strict float equality at LUT endpoint 1.1 failed by 1.14e-13 due to binary floating-point rounding. Test corrected to a bounded tolerance; source and algorithm unchanged.
- H02-02: ReShade FX compiler and hardware GPU unavailable. Classified NOT_RUN, not PASS.
- H02-03: P0 histogram preclear addresses counters only; persistent FA_State/FA_HistPrev cold-start and backend memory ordering remain open.
- H02-04: No actual full-frame shader render was executed. CPU sampling/image fixtures are independent models of selected functions.

- **CT-003 residual**: No GPU compiler or ReShade runtime available; texture marker first-use, resource reload and synchronization remain unverified. Sentinel collision is theoretically possible; marker is not an attestation primitive.

v0.4 CT-004: F23 residual motion inside the deadband reproduced then removed under proposed settle-to-rest policy; F24 neutral speed selection is inert after settle. No new unresolved CPU/static test failures. Native GPU certification pending.

v0.5 CT-005: Reproduced one-frame false scene-cut confirmation at 100..250ms in pre-change source oracle; candidate rejects first observation. No test failures recorded in two completed bounded campaigns. Native timing and GPU acceptance remain open.


### CT-006 v0.6.0 — 2026-11-01

CT-006 none in completed CPU harness campaigns; F40 intentional near-zero encoding discontinuity, F39 GPU/backend behavior not yet verified.

## CT-008 native compiler report
Operator supplied a compile-with-warnings excerpt: 19 X4000 warnings involving generated helper symbols and one X3571 pow warning; source-file positions are not confirmed because diagnostics reference generated shader buffers. The compiler succeeded, but source fingerprint and backend metadata were not captured in the excerpt. Mitigation is unverified pending a rerun.
