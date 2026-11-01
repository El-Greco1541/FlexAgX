# Roadmap
1. **v0.1 correction baseline:** F38 guard and F41 preclear, source/audit/CPU-probe checks.
2. **v0.2 cold-start assurance:** design and verify state/previous-hist initialization on the actual runtime.
3. **v0.3 source-semantics decisions:** deadband, superwhite, gamut/strength and transfer contract fixtures.
4. **v0.4 modular expansion:** independently executable pass equations, correct intermediate formats, API contracts and glue.
5. **Runtime acceptance:** ReShade FX compiler, GPU runs, cross-API fidelity, security and explicit release decision.
Production gate remains locked for every new material change until operator clearance.

## v0.2 effect treatment
Static and CPU harness complete. Next stage is a separate ReShade compiler/GPU runner; then first-use resource initialization and bounded fidelity evaluation. No production authority granted.

- v0.3.0: F18/F32 source mitigation and temporal harness completed; pending native acceptance. Expansion remains gated.

v0.4 candidate: F23/F24 source mitigation and tests; next F29/F36 semantic contract decision; F39/F40 gamut/encoding contract; native graphics certification.

v0.5 candidate: F29 two-observation scene-cut guard staged and CPU-tested; next Operator acceptance of F29/F36 semantics, native FX/GPU verification, then independent gamut/encoding research F39/F40.
