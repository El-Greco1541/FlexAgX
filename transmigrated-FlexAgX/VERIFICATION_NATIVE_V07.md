# CT-007 verification report (native-acceptance preparation)

**Result: preparation/tests PASS; native FX compilation and GPU execution NOT EXECUTED.** Production gate LOCKED.

- Candidate `.fx` SHA-256: `6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca` (unchanged from v0.6).
- Upstream FX SHA-256: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d` (unchanged).
- Regression tests: **135/135** pass (113 inherited + 22 new native-acceptance verifier tests).
- Existing harness self-tests: **16/16** pass.
- Fresh bounded CPU/static campaign: **61,607/61,607** checks pass; 350 simulated frames; seed `20261101`.
- ReShade FX compile: **NOT EXECUTED**.
- Native GPU render or visual comparison: **NOT EXECUTED**.
- Real native capture bundle: **NOT AVAILABLE**; a generated empty bundle properly fails verification.

A generated template and synthetic verifier-unit-test evidence **must not be represented as real native compiler or GPU evidence**. A fully populated record can be marked ready for *independent review*, never as GPU-certified. Full process-isolated per-phase evidence is available in the separate CT-007 test-evidence ZIP, not committed into the public repository.

See `docs/NATIVE_ACCEPTANCE.md`, `docs/CT007_NATIVE_ACCEPTANCE_STATUS.md`, and `native_acceptance/` for reproducible commands and acceptance boundaries.
