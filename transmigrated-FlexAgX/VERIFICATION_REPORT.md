# FlexAgX correction v0.3.0 — F18/F32 effect verification

**2026-11-01 · Staged; production gate LOCKED**

**Result:** 48/48 pytest PASS, two bounded harness campaigns PASS, 40,366/40,366 cumulative check executions, zero recorded failures.

| Seed | Simulated frames | Check executions | Failed |
| --- | ---: | ---: | ---: |
| 20261101 | 1,000 | 19,669 | 0 |
| 731234 | 2,000 | 20,697 | 0 |
| **Combined** | **3,000** | **40,366** | **0** |

The added temporal phase validates marker mismatch, state poison, scene-baseline normalization, uint32 frame rollover and disabled-gap behavior. All eight phases in both campaigns passed, including local HTTP and adversarial validation. The per-phase machine-readable report is `VERIFICATION_REPORT.json`. Full test evidence is included in the distribution ZIP; a compact summary can be staged in GitHub.

## Integrity

- Original upstream FX SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d` — **unchanged**.
- Corrected candidate SHA-256 `9116e0c2f4d13214b678f387bf05723348d0910117755e9a4c3de6addb894c68`.
- Original 8 passes and F41 preclear retained (9 total).

## Scope limit

The tests do **not execute the shader** in ReShade, nor prove compiler validity, actual GPU resource ordering, fresh texture initialization, pixel-level fidelity, or a strict effect reload lifecycle. The marker may theoretically collide with undefined texture data. F18/F32 is **source-mitigated, native-runtime-pending**, not fully closed. See `docs/TEMPORAL_BOOT_V03.md`.
