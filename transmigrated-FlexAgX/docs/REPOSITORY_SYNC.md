# Repository synchronization snapshot — 2026-11-01

**Repository:** [dastardlyrat/FlexAgX-CPU-server-simulation](https://github.com/dastardlyrat/FlexAgX-CPU-server-simulation)

**Scope:** housekeeping/documentation synchronization on the latest correction staging branch only. This snapshot records GitHub refs observed before this maintenance commit; consult GitHub for current heads. No upstream shader or executable code change is part of this sync.

## Verified branch baseline (prior to sync commit)

| Ref | Git SHA | Role |
| --- | --- | --- |
| `main` | `79c18ecdc013786076c8df7d2f45948fa5331428` | Upstream-derived default branch; unchanged |
| `stage/cpu-server-v0.4.0` | `247088f23962bfd59a210215673acff42b3a1e49` | CPU/API baseline |
| `stage/cpu-server-v0.5.0` | `e313cd59b8bd70f913eadb517040d685e6b5ef30` | Journal/idempotency baseline |
| `stage/code-transmigration-v0.1.0` | `9d0bc6f5902e737472a042d779b9a9305464c9cb` | Modular CPU/FX research |
| `stage/transmigrated-FlexAgX-v0.1.0` | `dd321f6c8b72987669a77e14f1c97e748ab981a4` | Shader correction baseline |
| `stage/transmigrated-FlexAgX-harness-v0.2.0` | `3c9144391e60d2753cf9d500b9a8a8cbdd1a3ac9` | Hardened effect harness |
| `stage/transmigrated-FlexAgX-corrections-v0.3.0` | `0760eeed7e3bac646f9fc4f2da71064d63906966` | CT-003 temporal boot |
| `stage/transmigrated-FlexAgX-corrections-v0.4.0` | `a6be49ad7ea7aa6d918cbf1d8a7b97b53226f103` | CT-004 deadband |
| `stage/transmigrated-FlexAgX-corrections-v0.5.0` | `9e3ea699152fce6c61cf9bf6555d04826f34a47c` | CT-005 scene cut |
| `stage/transmigrated-FlexAgX-corrections-v0.6.0` | `a472ffbcb21a52289cbb12b17e0e001800c31417` | CT-006 gamut; maintenance base |

## Existing review pull requests

- [PR #1](https://github.com/dastardlyrat/FlexAgX-CPU-server-simulation/pull/1): `stage/cpu-server-v0.4.0` → `main` — OPEN DRAFT.
- [PR #2](https://github.com/dastardlyrat/FlexAgX-CPU-server-simulation/pull/2): `stage/cpu-server-v0.5.0` → `stage/cpu-server-v0.4.0` — OPEN DRAFT.
- [PR #3](https://github.com/dastardlyrat/FlexAgX-CPU-server-simulation/pull/3): `stage/code-transmigration-v0.1.0` → `stage/cpu-server-v0.5.0` — OPEN DRAFT.

These are intentionally scoped to earlier workspaces. **No pull request exists for the corrected-shader v0.1–v0.6 sequence.** This synchronization does not retarget, merge, close or silently append those corrections to PR #1–#3.

## Source and evidence synchronization

- Source reference SHA-256: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- v0.6 corrected FX SHA-256: `6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca`.
- Most recent stored v0.6 evidence: 113 pytest, 16 harness self-tests, 125,545 counted checks across two synthetic campaigns. Original full evidence is retained separately; this sync does **not** claim new GPU testing.
- Manifest and SHA256SUMS will be rebuilt for the documentation-only change, and source/test file bytes must remain unchanged from the v0.6 baseline.
- Previously archived evidence filenames (including future-dated v0.4 CPU-server paths) are not retroactively rewritten; their chronological provenance must be reconciled separately.

## Controls and deferred actions

- No pruning, force-push, renaming, rebasing, release tag, PR merge, Docker deployment or shader release.
- No change to `main`, any earlier branch, the root README or root MIT license.
- Operator release gate remains **LOCKED**.
- F36/F40 color/exposure policies and native ReShade/GPU acceptance remain unresolved.
