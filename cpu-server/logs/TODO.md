# TODO — R4 forward work

- [x] Harden runner isolation, output limits, deadlines and evidence handling.
- [x] Enforce JSON sentinel, finite-number and strict count contracts.
- [x] Add adversarial cross-service fuzz corpus with pinned seed.
- [x] Verify state prepare/commit/abort, capacity and renderer-loss rollback.
- [x] Run final full campaign and separate maximum-frame torture.
- [x] Verify unchanged shader and application source hashes.
- [ ] Run on Windows/PowerShell and exercise process-tree cancellation.
- [ ] Run with actual ReShade FX compiler and target GPU backends.
- [ ] Introduce authenticated service-to-service transport and durable idempotency before any production proposal.
- [ ] Test network partitions, delayed commit ACK, and crash after commit without losing state provenance.
- [ ] Consider native per-request CPU watchdog isolation and memory ceilings.
- [ ] Triage outstanding F01–F43 independently; do not conflate harness PASS with those repairs.
