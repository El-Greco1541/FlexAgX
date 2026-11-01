# Correction ledger — first bounded pass

**Reference:** original FlexAgX 1.2, SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.  
**Candidate:** `shader/FlexAgX_transmigrated.fx`, SHA-256 `ff5f38cfc4f21bee6521b62aeb996eba6ed5bedd95c3745de82ac32d9199f3da`.  
**Status:** static source correction and CPU probe evidence only; no ReShade compiler or GPU execution.

| Entry | Prior evidence | Change made | What was verified | Unverified |
|---|---|---|---|---|
| CT-001 / F38 | Shader output invoked `atan2(b,a)` at achromatic origin; HuePS curved hue also unguarded | Explicit conditional guards around all three hue-angle sites; finite angle default 0 | Source structural checks, CPU origin/near-black probes, seeded angles | GPU compiler/driver behavior and visual parity |
| CT-002 / F41 | Histogram atomicAdd can execute before the first source-visible clear | Add **P0** histogram-clear compute pass before original P1; all 67 counters initialized each frame | Source ordering/coverage assertions and independent CPU reset-model tests | GPU resource/barrier correctness; state and previous-scene textures still need initialization proof |

**Important:** The derived FX now contains **nine** passes (P0 clear + the unchanged eight named original passes). It preserves all eight original pass implementations except the guarded hue calculations. The redundant histogram clear in P2 is kept to minimize semantic changes; performance is deliberately secondary to correctness.

**No blanket defect-repair claim:** F01–F43 remain independently triaged; only F38 and F41 received a bounded source edit. F41's runtime acceptance remains conditional until the ReShade effect compiles and passes first-use/reload GPU tests. The v0.5.0 CPU-server and code-transmigration workspaces are untouched; this new folder is separately staged.
