# TODO
- [x] Preserve original source and attribution
- [x] Guard F38 achromatic angular origin in FX P4/P8
- [x] Add F41 source-visible histogram preclear pass
- [x] Add bounded correction-probe HTTP API and injected ports
- [x] Unit, seeded property, and invalid JSON tests
- [ ] ReShade FX compiler validation on D3D11/D3D12/GL 4.3/Vulkan
- [ ] First frame and effect reload: FA_State / FA_HistPrev initialization proof
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
