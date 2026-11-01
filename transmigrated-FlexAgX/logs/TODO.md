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
