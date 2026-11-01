# Staged roadmap

1. R4 test-harness assurance — COMPLETE, read-only application (current).
2. Native backend and ReShade compilation — PENDING.
3. Bounded resource exhaustion and port-specific cross-platform verification — PENDING.
4. Distributed exactly-once/idempotency and authentication design — PENDING operator decision.
5. Production gate release — LOCKED; explicit Operator authorization required.

## v0.5.0 staged progress

Transaction receipt/replay and single-process SQLite atomic finalization implemented and tested. Production gate remains locked. Next: close legacy unsequenced API paths, authentication, disk quota/backup, controller multi-process/partition strategy.
