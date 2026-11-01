# Correctness boundaries and decision record

- ReShade shader FX 1.2 is immutable input. All eight passes are cataloged. Only CPU-side approximations run.
- `cpu-server/flexagx/` v0.5.0 remains the validated numerical foundation. Its modules are referenced by adapter rather than silently forked or rewritten. The new folder is a modular re-composition, not a new mathematical backend.
- `ObserverPort`, `TonePort`, `RendererPort`, `ImagePort`: independently replaceable, explicit method signatures. Temporal controller state lives in injected `SessionStore`.
- Orchestrator behavior is intentionally serial: check receipt, decode and validate, observe, prepare, build LUT, render, encode, finalize, then abort token cleanup. The non-exposure bypass is journaled.
- Correctness is prioritized over throughput: no speculative parallelism, caching assumptions, frame-dropping, loose schema coercion, performance targets or hidden approximation upgrades.
- At the tested JSON API boundary, missing and invalid inputs are rejected with typed sentinels. State has explicit defaults; pending transactions are bounded; errors must not commit state.
- Exact source-equation and partial GPU precision equivalence have **not** been established. No automatic ReShade integration is present.
- Existing `cpu-server/` still exposes legacy unsequenced controller endpoints, which are not imported as public endpoints by the new facade.
- No auth/TLS/multi-worker persistence; localhost-only experimentation; operators must not expose API publicly or commit real-session SQLite journals.
- Original license/copyright of El-Greco1541 (MIT) must be retained. GitHub ownership and commit metadata are public.
- Production gate remains LOCKED. This folder is staged research only, not promotion.
