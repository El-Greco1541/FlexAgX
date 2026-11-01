# Error / limitations register
| ID | State | Description |
|---|---|---|
| CT-E01 | Controlled | Hue `atan2` origin now guarded in source; GPU acceptance untested |
| CT-E02 | Controlled | Histogram preclear pass before P1 accumulation; GPU memory scheduling untested |
| CT-E03 | Open | FA_State and FA_HistPrev first-use are not proved initialized |
| CT-E04 | Open | No ReShade FX compiler/driver tests; no GPU parity |
| CT-E05 | Open | F39/F40 policy and perceptual correctness remain unresolved |
| CT-E06 | Explicit | API exposes correction probes only, not full image rendering or ReShade control |
