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
