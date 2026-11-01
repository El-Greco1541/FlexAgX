# Code Transmigration v0.1.0 — Verification

- **Local result:** 64 passed, 0 failed, executed with `python -m pytest tests -q`.
- The immutable FX 1.2 reference matches SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- Tests cover module mapping, ordinary frames, 48 seeded legal/bypass fixtures, no-null API error responses, malformed inputs, deterministic receipt replay, stale/conflicting frames, SQLite restart and renderer fault rollback.
- Original v0.5.0 project and root repository files are not modified.
- Source-content privacy scan passed; it cannot anonymize public GitHub ownership or commit metadata.
- **Not tested:** independent distributed network transport from this folder, GPU/ReShade compiler acceptance, Docker/PowerShell runtime, production authentication or exhaustive security.
- Production gate: LOCKED. Results apply to the local CPU approximation only.
