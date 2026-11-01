# FlexAgX v0.5.0 — correction-first verification

**2026-11-01 · STAGED · Production gate LOCKED**

**CT-005 / F29:** Prevent one-frame false scene-cut confirmation when `dt >= 100 ms`; require a previously observed candidate and accumulated time. **F36 remains unchanged.**

| Seed | Simulated frames | Counted checks | Result |
| --- | ---: | ---: | --- |
| 20261101 | 1,000 | 52,986 | PASS |
| 731234 | 2,000 | 54,014 | PASS |
| **Total** | **3,000** | **107,000** | **PASS** |

Additional **100/100 pytest**, **16/16 isolated harness self-tests**. Counts are check executions, not unique assertions or GPU frames. Source-mutation guards and 4,000 prior-candidate equivalence fixtures were run.

**Original FX:** byte-identical to El-Greco1541 1.2. **FX passes:** nine (one preclear plus eight original). Only the F29 source section was changed relative to v0.4.0.

**Unverified:** ReShade FX compilation, GPU execution, true effect reload, GPU storage ordering, visual parity, Operator acceptance of scene-cut semantics and the F36/F39/F40 policy decisions. Full per-case evidence is in the separately packaged evidence ZIP.
