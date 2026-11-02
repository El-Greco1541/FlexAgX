# FlexAgX — current roadmap (synchronized 2026-11-01)

**Policy:** correct first, expand second; prefer verified behavior and explicit module contracts over performance. All production work is gated by Operator approval.

| Milestone | Result | Standing |
| --- | --- | --- |
| v0.1 FX baseline | F38 hue guard, F41 histogram clear, provenance and CPU/API probe | Source/CPU tested; GPU open |
| v0.2 effect harness | Isolated seeded static, numerical, API and synthetic-frame tests | Tested; not GPU-equivalent |
| v0.3 temporal initialization | CT-003 marker and baseline reset | Source/CPU tested; GPU open |
| v0.4 adaptation deadband | CT-004 velocity settle to rest | Candidate; Operator policy acceptance open |
| v0.5 scene-cut confirmation | CT-005 two observations | Candidate; Operator policy acceptance open |
| v0.6 gamut correction | CT-006 post-blend gamut and F40 policy hold | Candidate; CPU/static tested |
| v0.7 native acceptance kit | Pinned SDR fixtures, toolchain probe, fail-closed log/screenshot evidence verifier | Local preparation tested; no GPU execution |
| Native target acceptance | Actual ReShade FX compiler, GPU frame/reload and color fixtures | **Blocked pending target runtime and Operator review** |
| Future expansion | Pass-level ports, API glue, color-space contracts | Deferred pending correctness acceptance |
| Production release | Requires explicit Operator clearance | **LOCKED** |

Current open decisions are maintained in [PENDING_DECISIONS](../docs/PENDING_DECISIONS.md); actionable tests are tracked in [TODO](TODO.md). Keep historical source-diff patches and test evidence immutable.
