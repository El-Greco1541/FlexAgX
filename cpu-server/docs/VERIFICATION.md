# Verification log and status

- `pytest` covers matrix inverses, transfer round trips, sampling phase/aliasing, controller session isolation, 1024-point LUT validation, renderer pipeline and zero-strength exact bypass.
- `tests/distributed_smoke.py` starts **five Uvicorn HTTP servers** and sends an actual PNG frame through every service, then terminates them.
- API source executes without `ReShade` or GPU, producing RGBA8 PNG output.
- **Not verified:** GPU compiler acceptance, shader/device interop, exact float32 texture sampling, HDR, colorspace references, empirical performance at real-time resolutions, production security, multi-process controller replication, distributed crash recovery.
- Version is `0.1.0` and gate remains locked.

This port is runnable and testable, but **must not be presented as a faithful GPU rewrite** without external reference images, captured controller traces, and per-pass GPU comparisons.
