# Transmigrated FlexAgX — effect harness v0.2.0 verification

**Research staging only • 2026-11-01 • production gate LOCKED**

**Outcome: PASS within static-source and CPU correction-probe scope. This is NOT a native effect render or GPU validation.**

| Campaign | Seed | Simulated frames | Counted checks | Failed |
| --- | ---: | ---: | ---: | ---: |
| First | 20261101 | 1,000 | 11,555 | 0 |
| Stress | 731234 | 2,000 | 12,583 | 0 |
| **Cumulative check executions** | | **3,000** | **24,138** | **0** |

Also: **40/40 local pytest tests pass**, including six new static-mutation tests, four harness acceptance tests and 30 inherited tests. They are not counted inside the 24,138 campaign checks. A 16-case harness self-test confirms rejection of corrupted evidence, missing files, mismatched seeds/phases, nonzero exits, timeouts and output flooding. Some cases repeat across campaigns; the cumulative count is **not** a count of distinct test vectors.

## Test inventory per campaign

| Phase | 1,000-frame run | 2,000-frame run | What it establishes |
| --- | ---: | ---: | --- |
| source | 17 | 17 | source SHA, pass order and guarded math checks |
| hue | 3,987 | 3,987 | origin thresholds, angle oracle and scaling |
| histogram | 2,520 | 2,520 | sampling model, uint32 phase, 64+3 counters, odd dimensions |
| interface | 1,181 | 1,181 | HTTP invalid inputs, sentinel responses and strict validation |
| metamorphic | 2,550 | 2,550 | LUT index bounds, reflection and additive histograms |
| torture | 1,027 | 2,055 | 2,000-frame *CPU histogram model*, not GPU frames |
| live_http | 273 | 273 | actual loopback FastAPI server, eight concurrent client threads |

## Source integrity

- Upstream shader (unmodified): `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- Corrected candidate shader (unmodified from v0.1.0): `ff5f38cfc4f21bee6521b62aeb996eba6ed5bedd95c3745de82ac32d9199f3da`.
- Exactly eight original shader passes remain in sequence, with one preclear pass inserted first (nine total).
- F38 achromatic `atan2` and F41 preclear constraints pass static tests; deliberately corrupted source examples are rejected.

## Runtime boundaries — REQUIRED follow-up, not passing tests

1. ReShade FX compilation and real D3D11/D3D12/OpenGL/Vulkan execution are **NOT RUN** because no ReShade compiler or GPU runtime is available in this environment.
2. F18/F32: `FA_State` and `FA_HistPrev` first-use and effect reload initialization remain unproven. The F41 histogram preclear does not resolve them.
3. GPU storage barriers, sampling and real image fidelity are unverified. The CPU histogram oracle reproduces selected source equations but is not a renderer.
4. F39 gamut and F40 encoding behavior remain pending policy decisions.
5. HTTP probes are local-only and unauthenticated; never expose them to untrusted networks.

**Scope verdict:** The tested correction interfaces, source invariants and 3,000 cumulative *simulated* frames pass. **Actual compiled/running FX effect: NOT TESTED.**
