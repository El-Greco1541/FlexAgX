# Pending correctness decisions before expansion

The following are not silently altered because they change user-visible semantics or lack a verified target backend.

1. **F18/F32:** FA_State / FA_HistPrev first-use initialization, effect reload and resumed framecount. Need source-visible bootstrapping supported by ReShade runtime, then actual GPU testing. CT-002 clears only histogram counters.
2. **F23/F24:** deadband/velocity carryover and adaptation-direction semantics. Decide freeze-vs-decay behavior with frame-sequence fixtures.
3. **F29/F36:** scene-cut correction and `AutoExposureStrength=0` internal state tracking. Define a time/step contract.
4. **F30/F31:** superwhite and negative input transfer function domain. Choose scene-referred vs encoded-display input contract.
5. **F39:** white-balance branch of strength mix can reintroduce out-of-gamut color. Choose whether to gamut-map the original branch or defer white balance until after blending.
6. **F40:** encoding mismatch at exactly 0% vs positive infinitesimal strength. Choose identity bypass or independent output conversion; cannot satisfy both without a policy.
7. **F19:** actual ReShade 5.9+ compilation and required backend behavior are still unverified.
8. **API extension:** promote correctness probes into full render-stage replaceable server ports only after per-stage numerical fixtures and operator decisions. No GPU/plugin bridge or external ingress authorized.

Research-only, production gate locked.
