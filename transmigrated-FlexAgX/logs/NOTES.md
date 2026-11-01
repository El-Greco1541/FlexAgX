# Research notes
- Correctness over speed: a new P0 clear pass is intentional overhead. Existing P2 clear is not removed.
- Fail closed on out-of-domain API input and do not echo user payloads.
- Modularity is through injected pure ports; actual GPU pipeline remains independent.
- No prior shader defects outside F38/F41 are claimed corrected.
- All values in archived JSON evidence avoid null and nonfinite outputs.

## Effect harness result
Source references and shader remain byte-identical. Seven isolated phases and live HTTP tests passed at seeds 20261101 and 731234, 1,000/2,000 simulated frames respectively; 24,138 counted checks. More than one campaign reuses parts of the test corpus.

- v0.3.0 F18/F32: dual sentinel + split 32-bit frame marker, validation before retained-state use; CPU model and source tests PASS; native FX acceptance pending.

v0.4 CT-004: Deliberately minimal FX S5 edit, keeping rate limit and phase structure. A CPU oracle is not an FX runtime. Original source remains immutable.

v0.5 CT-005 is a deliberate one-line conditional change in S6, with a captured previous-candidate flag. No pass additions and no changes to F36 or gamut/encoding. Synthetic probes are not native GPU evidence.


### CT-006 v0.6.0 — 2026-11-01

CT-006/F39: bounded post-strength Oklab gamut remap, unchanged in-gamut; F40 exact encoded 0% bypass unchanged and noted discontinuity. SHA-256=6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca. GPU unverified.
