# Security and production boundaries

The request to transmigrate the authorized source is interpreted as permission to create **staged development artifacts** only. The original remains immutable in the package. No production clearance is inferred.

**Current security posture:** loopback-only developer gateway via Compose, isolated microservice network, untrusted input validation at individual services. No authentication or transport encryption. In-memory sessions only. HTTP ingress is not suitable for remote exposure. Since frames may contain private or confidential information, treat them as sensitive inputs; use local endpoints, no automatic external uploads.

## Required before deployment

- Operator-approved API and behavioral contracts; versioned immutable artifact.
- Authentication, authorization and per-session identity isolation.
- Encryption and local endpoint protection; explicit data retention and audit design.
- Idempotent frame sequencing, replay protection, transactional or recoverable state advancement.
- Resource limits beyond image dimensions, latency budgeting, high-rate packet/stream transport.
- GPU and CPU reference comparison under representative game frames and color profiles.
- Relevant ReShade FX compiler checks, actual API backend tests and fail-closed runtime handling.
- Hardened containers, SBOM/dependency scanning, license review and reproducible release process.

## Technical migration hazards

- API calls do not correspond one-to-one to GPU frame execution.
- Changing `OverallStrength` or `DebugView` changes whether state progresses; preserving state behavior is a contract.
- Session resets, scene cuts and frame timing must be deterministic with the chosen state store.
- CPU float64 vs GPU shader float32 and texture format quantization prevents a blanket fidelity claim.
- Raw `RGBA8 PNG` is not a scene-referred or HDR frame buffer.
- Networked microservers add failure and synchronization surfaces that did not exist in a single GPU effect.
