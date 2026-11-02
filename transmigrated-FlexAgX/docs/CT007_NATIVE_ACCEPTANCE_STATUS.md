# CT-007 native acceptance status

**State:** PREPARED / UNVERIFIED ON GPU. **Production gate:** LOCKED.

- Shader candidate: v0.6.0 unchanged, SHA-256 `6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca`.
- Original shader unchanged: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- v0.7 components: fixture producer, FX toolchain discovery, structured collection plan, redacted evidence schema, fail-closed file/PNG verifier and bypass identity comparison.
- Missing: real ReShade FX compile log, device/driver/backend measurements, cold/reload traces, float-capable gamut capture, HDR input contract and independent operator attestation.
- No native artifacts were invented, embedded or committed.
- Earlier v0.6 static/CPU campaign: 113/113 tests and 125,545 repeated harness checks. Those historical results are not regenerated or presented as GPU evidence.
- CT-007 tests are separate, in `tests/test_native_acceptance.py`. The verifier never produces a `GPU_CERTIFIED` or `PRODUCTION_APPROVED` status, even when test fixtures simulate complete evidence.

See [NATIVE_ACCEPTANCE](NATIVE_ACCEPTANCE.md) for the reproducible procedure and minimum test matrix.
