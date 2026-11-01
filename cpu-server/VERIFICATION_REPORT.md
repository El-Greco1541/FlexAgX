# FlexAgX CPU Server v0.5.0 — Verification report

**Date:** 2026-11-01  
**Stage:** experimental, production gate LOCKED  
**Harness:** PASS — **1060 / 1060** counted checks, seed `20261104`, **1000** sequential torture frames  
**Reference shader:** SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d` — unchanged from El-Greco1541 release 1.2

| Phase | Checks | Outcome |
| --- | ---: | --- |
| static_audit | 1 | PASS |
| harness_selftest | 1 | PASS |
| regression_and_assurance | 53 | PASS |
| validation | 333 | PASS |
| metamorphic | 85 | PASS |
| adversarial | 567 | PASS |
| torture | 5 | PASS |
| distributed_guarded | 4 | PASS |
| distributed_v05 | 8 | PASS |
| ackdrop_v05 | 3 | PASS |

## Demonstrated v0.5.0 behaviors

- Matching frame replay returns exactly the recorded response without reapplying temporal controller state.
- Conflicting duplicate or stale frame indices fail closed.
- Zero-strength bypass is journaled, retaining exact identity output without exposure-state progression.
- Controller state and frame receipt share an atomic SQLite transaction when durable path is configured.
- A controller restart replays committed output and rejects uncommitted state.
- A downstream renderer failure does not commit the candidate state.
- A local forwarding proxy that **drops a successful finalize acknowledgment** triggers gateway receipt recovery without a double commit.
- Seeded fuzz, image property tests, and both inherited/expanded live-service fault suites passed.
- Structural audit, harness watchdog self-test and pinned source hashes passed.

## Known limitations / open errors

1. Legacy `/v1/control/step` and `/v1/control/commit` remain unsequenced compatibility endpoints. Do not allow external access.
2. In-memory mode is still the default without `FLEXAGX_STATE_DB`. Durable mode requires an explicit local SQLite file/volume; only one controller worker is supported.
3. SQLite persists logical receipts but database file size, disk quota, backup, crash-corruption recovery, and process-level native resource budgets remain operational responsibilities.
4. Replayed records are bounded (512, total serialized receipts <=128 MiB, per-record <=20 MiB). Once evicted, old frames fail closed rather than replaying.
5. No authentication, cross-host consensus, TLS, WAN partition certification, Docker/Windows certification, or ReShade/GPU equivalence has been established.
6. Previous v0.4 archived reports contain filenames with dates later than this report; they remain historical artifacts and are not relied upon for this v0.5 verdict.

**Execution evidence note:** The v0.5 harness wrote its verified final PASS report. Its enclosing 1,000-frame invocation subsequently hit an external command-session timeout; the JSON evidence was independently read and validated, and no service processes remained running. Report this distinction rather than claiming the wrapper returned a clean exit code.
