# v0.6.0 verification — F39 gamut correction and F40 policy hold

Date: 2026-11-01. Status: **PASS (CPU + static + local HTTP only)**. Production gate: **LOCKED**.

- Python regression suite: **113 / 113** tests passed.
- Isolated harness self-tests: **16 / 16** passed.
- Seed 20261101 at 1,000 synthetic frames: **62,274 / 62,274** checks passed.
- Seed 731234 at 2,000 synthetic frames: **63,271 / 63,271** checks passed.
- Cumulative **125,545 / 125,545 checks passed** across repeated and independent phases; not 125,545 unique tests.
- Original shader SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d` unchanged.
- Current shader candidate SHA-256 `6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca`.

F39: post-blend conditional gamut mapper source structure, in-gamut identity, out-of-gamut bounds and CPU Oklab hue witnesses passed. It is **not GPU-certified**. F40: tests establish that exact 0% encoded bypass remains, and a near-zero cross-encoding discontinuity is **not** removed. Retaining this policy requires Operator acceptance.

Raw case-level reports are in the separate full-evidence ZIP. Summary JSON in `harness/evidence/V06_...`.

**Not tested:** ReShade FX compiler, actual GPU image output, backend storage barriers, proper color-profile management, platform-specific drivers, native float32 precision and visual quality.
