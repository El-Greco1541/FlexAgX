# Current correction TODO — synchronized 2026-11-01

This list is the **current** status for the v0.6.0 FX candidate. Completed work means source/static/CPU verification only, not native GPU acceptance. Earlier item-by-item progress remains available in Git history and [correction ledger](../docs/CORRECTION_LEDGER.md).

## Completed (staged, not promoted)

- [x] Preserve unmodified upstream 1.2 FX and MIT attribution.
- [x] F38 achromatic hue guards, F41 histogram preclear (CT-001/002).
- [x] F18/F32 temporal marker and cold-baseline source mitigation (CT-003).
- [x] F23/F24 settle-to-rest deadband source candidate (CT-004).
- [x] F29 two-observation scene-cut source candidate (CT-005).
- [x] F39 conditional post-mix gamut source candidate (CT-006).
- [x] Preserve F36 state-tracking and F40 exact encoded zero-strength bypass semantics.
- [x] Execute v0.6.0 regression tests, harness self-tests and two recorded synthetic campaigns.
- [x] Synchronize current README, roadmap, inventory hashes and repository branch/PR record without changing FX or code.

- [x] Build CT-007 native-acceptance capture plan, source-pinned fixtures, integrity verifier and negative-test suite; no GPU claim.

## Open: correctness acceptance

- [ ] Obtain explicit Operator acceptance of CT-004, CT-005 and CT-006 behavioral policies.
- [ ] Decide F36 zero-strength internal tracking and F40 output-encoding continuity contracts.
- [ ] Define F30/F31 negative/superwhite input domain and transfer policy.
- [ ] Compile candidate under actual ReShade FX and record the compiler diagnostics.
- [ ] Exercise D3D11/D3D12/OpenGL/Vulkan backends as available; document supported and unsupported targets.
- [ ] Verify first-frame/reload initialization, retained histogram/state, effect toggling and GPU barriers.
- [ ] Compare GPU frames with CPU fixtures across linear/encoded inputs, hue, exposure and gamut boundary cases.
- [ ] Evaluate native float32 stability and instrument resource/performance budgets after correctness is established.
- [ ] Build full modular pass-level API glue only after source fidelity and per-stage fixtures pass acceptance.
- [ ] Obtain explicit Operator release authorization before any merge or deployment.

**Status: STAGED. Production gate LOCKED.**
