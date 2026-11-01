# Research notes — code transmigration 0.1.0

- Engineering decision: preserve the upstream 1.2 FX shader byte-for-byte; do not reinterpret ReShade source as an HTTP-native shader.
- Existing v0.5.0 CPU numerical components are re-used by explicit ports rather than producing a second unverified math fork.
- The orchestration sequence is serial and fail-closed, with controller state commit only after successful image output validation.
- No externally reachable server, compiled FX runtime, or GPU behavior is claimed.
- Fidelity is limited by the existing CPU approximation and its grouped P3–P8 renderer.
- API metadata advertises all eight FX passes and current port ownership, not an invented fully decomposed GPU pipeline.
- Local first-party test corpus includes seeded images, invalid JSON and PNG data, replay, ordering, bypass, renderer failure and restart recovery.
