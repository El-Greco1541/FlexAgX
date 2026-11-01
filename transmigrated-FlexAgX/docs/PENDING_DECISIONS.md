# Pending correctness decisions before expansion

The following are not silently altered because they change user-visible semantics or lack a verified target backend.

1. **F18/F32:** CT-003 now includes marker validation, finite state seeds and a cold histogram baseline. Native ReShade compilation, first-frame and effect-reload resource-lifetime and marker-collision acceptance remain **open**. CT-002 clears the histogram counters separately.
2. **F23/F24:** CT-004 stages *settle-to-rest* within inclusive deadband with finite CPU/static tests. This is an explicit candidate policy; Operator acceptance and native GPU/visual testing are **pending**, rather than treating the prior freeze-versus-decay ambiguity as silently closed.
3. **F29/F36:** CT-005 stages two-observation scene-cut confirmation while preserving the 100ms time threshold. F36 internal scene tracking with `AutoExposureStrength=0` is unchanged; Operator acceptance and native frame-time/GPU tests remain pending.
4. **F30/F31:** superwhite and negative input transfer function domain. Choose scene-referred vs encoded-display input contract.
5. **F39:** CT-006 stages a post-blend chroma-boundary mapper which preserves already in-gamut composites. Operator approval of that proposed color strategy and native GPU/visual acceptance remain outstanding; alternative original-branch mapping is not ruled out.
6. **F40:** CT-006 explicitly retains exact 0%-strength encoded bypass and documents that input/output encoding mismatch, temperature or dithering may cause a near-zero transition. Select a different slider/output-conversion policy separately if continuity is required; no F40 semantic change is approved.
7. **F19:** actual ReShade 5.9+ compilation and required backend behavior are still unverified.
8. **API extension:** promote correctness probes into full render-stage replaceable server ports only after per-stage numerical fixtures and operator decisions. No GPU/plugin bridge or external ingress authorized.

Research-only, production gate locked.
