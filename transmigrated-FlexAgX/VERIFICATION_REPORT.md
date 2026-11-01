# Verification — Transmigrated FlexAgX v0.1.0

**2026-11-01.** **PASS**: 30 local pytest tests; within these, 256 deterministic hue probes and 256 deterministic histogram probes run. These repeated cases are **not** counted as separate pytest tests.

- Immutable upstream shader SHA-256: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d` — matches release 1.2.
- Derived FX candidate SHA-256: `ff5f38cfc4f21bee6521b62aeb996eba6ed5bedd95c3745de82ac32d9199f3da`.
- Original 8 passes retained in order, with one added P0 preclear pass (total 9).
- Static source assertions prove intended guard and clear-pass placement in this artifact.
- FastAPI local correction probes validate strict inputs, typed sentinel failure, bounded histogram population, zero-origin handling and injectible ports.
- Malformed/NaN/Infinity **inputs** were rejected with bounded sentinel output; no JSON null or nonfinite values emitted in recorded metadata.
- Static privacy scan of 23 project files found no listed credential patterns or private workspace paths.
- Full ReShade compiler, D3D11/D3D12/Vulkan/OpenGL GPU execution, first-frame persistence and FX numerical/visual parity: **NOT TESTED**.
- F41 is a source-level remediation pending GPU synchronization verification. `FA_State` and `FA_HistPrev` initialization remain open.
- Legacy `cpu-server/` and `code-transmigration/` remain separate; no merge or deployment performed.

**Test command**: `python -m pytest -q tests` (run within `transmigrated-FlexAgX/`). Production gate LOCKED.
