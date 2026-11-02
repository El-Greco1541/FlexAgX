# v0.8.0 native warning triage verification

- **Native evidence received:** compiler success reported by Operator, 1.865 seconds, X4000 ×19, X3571 ×1; file hash, ReShade version and GPU backend missing. No raw log or machine path committed.
- **Candidate correction:** explicit nonnegative pow operand in the strength roll-off function. Behavior preserved for legal `GamutRolloffStart` and gamut-roll-off inputs.
- **Not asserted:** X4000 resolved, X3571 eliminated, v0.8 compiled natively, correct GPU rendering or production authorization.
- **Local regression (this revision):** 151/151 pytest tests PASS; 16/16 harness self-tests PASS; one 350-frame seeded CPU/static campaign PASS at 61,607/61,607 counted checks (seed 20261101). These are not native ReShade/GPU tests.
- **Remaining acceptance:** recompile v0.8 on target system, record digest and backend/version, compare warning inventory, run capture matrix and first-frame/reload tests.
