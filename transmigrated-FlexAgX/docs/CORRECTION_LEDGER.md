# Correction ledger — first bounded pass

**Reference:** original FlexAgX 1.2, SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.  
**Candidate:** `shader/FlexAgX_transmigrated.fx`, SHA-256 `9116e0c2f4d13214b678f387bf05723348d0910117755e9a4c3de6addb894c68`.  
**Status:** static source correction and CPU probe evidence only; no ReShade compiler or GPU execution.

| Entry | Prior evidence | Change made | What was verified | Unverified |
|---|---|---|---|---|
| CT-001 / F38 | Shader output invoked `atan2(b,a)` at achromatic origin; HuePS curved hue also unguarded | Explicit conditional guards around all three hue-angle sites; finite angle default 0 | Source structural checks, CPU origin/near-black probes, seeded angles | GPU compiler/driver behavior and visual parity |
| CT-003 / F18/F32 | `FA_State` and `FA_HistPrev` were read without a validated lifecycle or first-use scene baseline | Introduce `FA_TemporalBoot` marker with version sentinels and split uint32 frame index; validate prior state; initialize each retained field; seed `FA_PrevSh` with current histogram on cold-start; commit marker after state/history writes | 48 pytest plus 40,366 deterministic check executions; marker poison/restart/gap/wrap/mutation tests | FX compilation and native backend texture-lifetime, barriers, reload behavior; marker validation is defensive rather than a cryptographic/absolute proof |
| CT-002 / F41 | Histogram atomicAdd can execute before the first source-visible clear | Add **P0** histogram-clear compute pass before original P1; all 67 counters initialized each frame | Source ordering/coverage assertions and independent CPU reset-model tests | GPU resource/barrier correctness; state and previous-scene textures still need initialization proof |

**Important:** The derived FX now contains **nine** passes (P0 clear + the unchanged eight named original passes). It preserves all eight original pass implementations except the guarded hue calculations. The redundant histogram clear in P2 is kept to minimize semantic changes; performance is deliberately secondary to correctness.

**No blanket defect-repair claim:** F01–F43 remain independently triaged; only F38 and F41 received a bounded source edit. F41's runtime acceptance remains conditional until the ReShade effect compiles and passes first-use/reload GPU tests. The v0.5.0 CPU-server and code-transmigration workspaces are untouched; this new folder is separately staged.

## CT-003 decision boundary

The F18/F32 corrective source change uses an explicit **temporal marker**, not a guaranteed initial texture fill. Its magic values and consecutive framecount checks allow a safe fallback for uninitialized, stale, or corrupted retained textures. However, a marker could theoretically collide with arbitrary initial contents; neither this model nor the static harness proves that memory is zeroed or that backend resource lifetimes match the assumptions. A native ReShade restart/reload test is a hard acceptance requirement.

A disabled frame does not refresh the marker, so the next active frame is treated as a cold start. A valid retained controller state is reused only for a consecutive frame. Framecount is stored in two exact 16-bit float limbs and interpreted modulo 2^32; no float32 precision collapse is introduced by the marker. The source has nine passes, unchanged by CT-003.

## CT-004 / F23-F24 — v0.4.0 bounded candidate

- Source change: inclusive deadband (`abs(target - x) <= Deadband`) now settles `v=0` and holds `x` exactly, bypassing direction/speed selection until the error exits the band.
- Untouched: outside-deadband dynamics, scene-cut correction (F29), zero-auto-exposure internal tracking (F36), gamut/encoding policy (F39/F40) and all other FX passes.
- Evidence: 79 pytest tests and 55,570 cumulative deterministic CPU/static check executions; source mutation rejected; GPU unverified.
- **Operator decision:** settle-to-rest is a candidate policy justified by the UI deadband tooltip. Do not promote or conflate with external approval. See `docs/CT004_DEADBAND_SETTLING.md`.
- Candidate SHA-256: `abbb4cf5e5ca97cdcfc694567e8e4b462bf19634a2b4d3d60d83d73cac184dde`. Upstream remains `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.

## CT-005 / F29 — v0.5.0 candidate

- A single slow frame no longer causes scene-cut confirmation; a pre-existing discrepant observation is required.
- Existing persistence threshold, histogram baseline handling and applied exposure rate limits are retained.
- F36 (zero automatic exposure contribution while internal state may track) is unchanged and remains a policy holdout.
- CPU/static tests: 100 pytest; 107,000 counted deterministic checks across two runs; 16 harness self-tests; native GPU not executed.
- Corrected candidate SHA-256: `311941a715b8396e01c3f57df850c6a28207cf82c2a6f074be0a4cf95e3bfef5`; upstream FX SHA-256 remains `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- Operator choice of scene-cut temporal semantics and GPU acceptance remains required. See `docs/CT005_SCENE_CUT_CONFIRMATION.md`.
