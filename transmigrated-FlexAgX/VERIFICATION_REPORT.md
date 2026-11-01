# FlexAgX staged correction v0.4.0 — Verification

**Date:** 2026-11-01. **Subject:** CT-004/F23-F24 proposed deadband velocity settling. **Production gate:** LOCKED.

| Campaign | Synthetic frames | Counted CPU/static checks | Failed |
| --- | ---: | ---: | ---: |
| Seed 20261101 | 1,000 | 27,271 | 0 |
| Seed 731234 | 2,000 | 28,299 | 0 |
| **Total** | **3,000** | **55,570** | **0** |

Additional: **79/79 pytest passed; 16/16 bounded-runner self-tests passed**. The check counts are executions, not unique test definitions; they include existing inherited suites and 7,602 adaptation-check executions per campaign. See machine-readable report for precise per-phase counts; do not treat these as distinct bugs fixed.

**Source:** Original FlexAgX 1.2 upstream FX unchanged and SHA-256 pinned. Candidate retains nine FX passes; the S5 deadband fragment is the only shader edit relative to v0.3.0.

**Acceptance boundary:** CPU and static assertions are evidence of the proposed source-level contract only. FX compiler, ReShade GPU backend, storage ordering, color/pixel fidelity, startup/reload, scene-cut and gamut/encoding behavior remain unverified or undecided. See `docs/CT004_DEADBAND_SETTLING.md`.
