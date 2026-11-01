# TODO
- [x] Preserve original source and attribution
- [x] Guard F38 achromatic angular origin in FX P4/P8
- [x] Add F41 source-visible histogram preclear pass
- [x] Add bounded correction-probe HTTP API and injected ports
- [x] Unit, seeded property, and invalid JSON tests
- [ ] ReShade FX compiler validation on D3D11/D3D12/GL 4.3/Vulkan
- [x] Add F18/F32 defensive source-level marker and cold-baseline initialization; CPU/static verified
- [ ] F18/F32: prove first frame, effect re-enable and reload behavior on ReShade GPU, including storage barriers
- [ ] Resolve F39 and F40 visual/encoding contracts with operator
- [ ] F23/F24 deadband/velocity behavior contract and tests
- [ ] Migrate accepted corrections into independent CPU pass implementations
- [ ] Test actual GPU vs CPU numerical parity before expansion

## Effect harness v0.2.0
- [x] Isolated seven-phase static/CPU/HTTP harness with per-run evidence and deadlines
- [x] 40/40 pytest, 24,138 seeded check executions across 1,000 and 2,000 frames
- [x] FX mutation guards and proof of fail-closed harness selftests
- [ ] Native ReShade compiler / actual GPU frame capture and independent color comparison
- [ ] Resolve FA_State and FA_HistPrev first-use/reload initialization
- [ ] Decide gamut/encoding F39/F40 contracts before source modification

## v0.3.0 F18/F32
- [x] Add finite state defaults and previous-scene baseline for invalid startup marker
- [x] Validate 32-bit frame sequencing across wrap, gaps, corruption and replay-like repeated frame indices
- [x] Structural source mutation regression and isolated temporal harness phase
- [ ] Native FX compilation and ReShade GPU startup/reload acceptance
- [ ] Strict reset-on-reload mechanism if a backend preserves resources without a lifecycle signal

## v0.4.0 CT-004 F23/F24
- [x] Reproduce residual velocity drift with v0.3 source oracle
- [x] Propose a deadband settle-to-rest source correction; zero velocity when inside band
- [x] Verify unchanged outside-band equations, deadband=0 and source mutation sensitivity
- [x] Run bounded CPU, HTTP and adversarial harness campaigns
- [ ] Obtain Operator acceptance of settle-to-rest versus gradual decay semantics
- [ ] Native ReShade compilation and first-frame/reload GPU tests
- [ ] F29/F36 scene-cut and zero-strength policy decision; F39/F40 gamut/transfer policy decision

## v0.5.0 CT-005 F29/F36
- [x] Reproduce one-frame slow-timestep premature scene cut in legacy S6.
- [x] Require prior discrepant observation as well as time threshold.
- [x] Test single-frame spikes, interrupts, persistent cuts, max dt and strict threshold.
- [x] Preserve F36 zero-auto-strength tracking and manual EV policy without changing it.
- [x] Run bounded CPU/static harness at 1,000 and 2,000 frames.
- [ ] Operator acceptance of two-observation scene-cut policy.
- [ ] Native ReShade GPU/FX compilation, visual and frame-timing tests; test freeze/re-enable/reload.
- [ ] F39/F40 gamut and output encoding decisions.


### CT-006 v0.6.0 — 2026-11-01

[x] CT-006 F39 post-mix source guard, numerical model, mutation tests and seeded fuzz. [ ] F40 output-continuity policy selection. [ ] Native ReShade FX compiler and visual acceptance. [ ] Driver/backend texture validation.
