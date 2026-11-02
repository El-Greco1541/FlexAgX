# CT-008 — Native compilation warnings: evidence and bounded mitigation

**Input:** Operator-supplied native ReShade compilation excerpt, November 1, 2026. The message reports compilation **in 1.865 seconds with warnings**. The source/build hash, ReShade version, backend, driver, and full generated shader code were **not** supplied. Do not infer any of those parameters from a game path.

**Source candidate before mitigation:** v0.7.0 kit containing the v0.6.0 shader, SHA-256 `6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca`.

## Warning inventory

- **X4000 ×19:** potential uninitialized-value use at *generated-backend* locations. The messages name generated helper identifiers: `F__FA_Decode` (5), `F__FA_Encode` (2), `F__FA_ComposedCurve` (1), `F__FA_Native` (4), `F__FA_Dn` (5), `F__FA_WhiteBalance` (1), `F__FA_ConstrainGamutAfterMix` (1). These may be compiler-generated function aliases rather than user-declared local variables. The excerpt cannot prove harmlessness or demonstrate a definite uninitialized path.
- **X3571 ×1:** a pow() operation may receive a negative base. The FX source includes a gamut roll-off `pow(t, _FA_GAMUT_P)` whose domain was guaranteed by conditional control flow but not encoded in the operand. CT-008 guards this specific candidate as `pow(max(t, 0.0), _FA_GAMUT_P)`; **the excerpt does not establish that this is the exact generated warning location**.

The log also contains changing `Shader@0x...` addresses and compiler-generated positions. None is a validated original `.fx` line reference. Addresses and workstation paths are deliberately not stored in this public repository.

## Correction and proof obligations

1. Only the gamut pow's inner base is explicitly clamped. For the legal UI range `0.60 <= k <= 0.95`, the branch condition `x > k` guarantees `(x-k)/(1-k) > 0`. For all such inputs the old and new expressions are identical. A 5,000-case deterministic CPU oracle confirms this. No speed optimizations.
2. Do **not** write arbitrary initializers to `F__...` helpers: those names are not confirmed source variables, and doing so may hide a real bug. Source-level groupshared synchronization and state boot remain open GPU-acceptance questions.
3. Compile the new FX on the **same machine and renderer backend**, capture full version/driver metadata, diff X4000/X3571 counts, and inspect the corresponding generated HLSL/GLSL if warnings persist.
4. Run first-frame, reload, histogram-clear and SDR fixture captures before accepting the effect. The prior CPU/static passing tests are not sufficient.

## Portable, privacy-safe warning parser

```bash
python -m native_acceptance.compiler_warnings --input compiler-local.log --output warning-summary.json
```

This reports warning counts, function identifiers and generated line numbers, and discards file paths and pointer values. The JSON intentionally keeps `gpu_certified=false` and `native_warning_free=false` until independently proven. Do **not** publish the original log or real captures without review.

**Disposition:** Native compilation reported with warnings; one domain guard staged; warning remediation and GPU fidelity unverified. Production gate LOCKED.
