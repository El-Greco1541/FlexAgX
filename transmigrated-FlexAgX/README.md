# Transmigrated FlexAgX — correctness-first shader research

**Current shader candidate: v0.8.0 (CT-008 domain guard) · Native acceptance tooling: v0.8.0 · Production gate: LOCKED**

This is an independent, source-traceable research adaptation of [El-Greco1541/FlexAgX](https://github.com/El-Greco1541/FlexAgX), release 1.2, licensed under MIT. It preserves the upstream FX file unchanged in `reference/` and places all experimental edits in `shader/`. The original author has not endorsed this project. **Operator reports that v0.7 shader compiled in ReShade in 1.865 seconds with 20 warnings; executable source identity/backend not yet corroborated, v0.8 not yet compiled natively, and GPU rendering acceptance is pending.**

The primary objective is correctness, modularity and explicit testing. Throughput and rendering speed are subordinate to source fidelity and verified behavior. The `correction_api/` service is a bounded mathematical probe, **not** an executable replacement for the shader or a production API server.

## What is current

| Aspect | Verified staging status |
| --- | --- |
| Original shader | Byte-identical to FlexAgX 1.2; SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d` |
| Corrected candidate | `shader/FlexAgX_transmigrated.fx`; SHA-256 `2700deed3c2ff76b439e2efa70d2c41f7b94cccd5efb4123afbd3623127960ec` |
| Passes | Nine source passes: P0 histogram preclear plus the original eight in their existing order |
| Historical v0.6 evidence | 113/113 pytest tests, 16/16 harness self-tests and 125,545 cumulative checks in two earlier CPU/static campaigns; see v0.8 test report for fresh checks |
| Execution scope | Local static/CPU checks; operator-provided native ReShade compile-with-warnings excerpt for earlier shader, pending source-hash/backend identification |
| Deployment | None; research branch only, gate locked |

The totals are **counted check executions**, not distinct tests. These results were obtained on the v0.6.0 shader candidate before this documentation-only synchronization; no new GPU evidence is claimed. See [verification](VERIFICATION_REPORT.md) and [evidence summaries](harness/evidence/).

## Correction history — source behavior versus acceptance

| Stage | Findings | Candidate change | Acceptance boundary |
| --- | --- | --- | --- |
| v0.1 · CT-001/CT-002 | F38/F41 | Guard achromatic hue angles; clear histogram counters before atomic accumulation | CPU/static tests; GPU pass ordering and barriers unverified |
| v0.3 · CT-003 | F18/F32 | Validated temporal boot marker, finite controller defaults and initial histogram baseline | GPU resource lifetime, reload and collision behavior unverified |
| v0.4 · CT-004 | F23/F24 | Settle retained velocity within an inclusive deadband | Requires Operator behavioral approval and native visual tests |
| v0.5 · CT-005 | F29 | Require at least two discrepant observations before scene-cut confirmation | Requires Operator behavioral approval and native frame-time tests |
| v0.6 · CT-006 | F39 | Post-strength-blend gamut containment through bounded Oklab chroma search | CPU/source-verified; GPU color correctness and rendering unverified |
| v0.8 · CT-008 | X3571/X4000 | Explicit nonnegative operand in gamut roll-off pow; privacy-safe compiler warning triage | Fresh ReShade compilation of v0.8 required; X4000 remains unresolved |
| Policy hold | F36/F40 | Existing internal tracking at zero auto-exposure and exact 0%-strength encoded bypass preserved | Explicit Operator decision required before behavioral change |

**Do not call the FX shader GPU-corrected or production-ready.** Earlier individual test totals are recorded in Git history and versioned reports; the v0.6.0 totals above are the current campaign reference. The original 43-finding audit does not imply all findings were addressed.

Detailed source edits and decision boundaries: [Correction Ledger](docs/CORRECTION_LEDGER.md), [CT-004](docs/CT004_DEADBAND_SETTLING.md), [CT-005](docs/CT005_SCENE_CUT_CONFIRMATION.md), [CT-006](docs/CT006_F39_GAMUT_AND_F40_ENCODING.md), and [Pending Decisions](docs/PENDING_DECISIONS.md).

## Build and test the available CPU/API probes

From `transmigrated-FlexAgX/` with Python 3.10+:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
python -m harness.selftest
python -m harness.runner --seed 20261101 --frames 1000
python -m harness.runner --seed 731234 --frames 2000
```

The isolated harness intentionally performs repeated deterministic, seeded, adversarial, structural and local HTTP checks. It requires a writable temporary directory; transient data should not be committed. A full campaign is a test execution, **not** GPU acceptance. The original FX file is validated against its preserved hash; changes to source pins require an explicit correction entry.

To expose the small **localhost-only correction probe** for development:

```bash
python -m uvicorn correction_api.api:app --host 127.0.0.1 --port 8081
```

The probe supports `GET /health`, `GET /v1/capabilities`, `POST /v1/correction/hue`, and `POST /v1/correction/histogram`. Its contracts reject malformed wire values with typed results and do not ingest a live ReShade framebuffer. The independent `cpu-server/` directory contains the fuller CPU image API and its separate transaction journal; `code-transmigration/` contains modular orchestration research. Neither is replaced by this shader candidate.

## CT-007: native acceptance preparation (v0.7.0)

The candidate `.fx` source remains **byte-identical to v0.6.0**. The new [Native Acceptance Protocol](docs/NATIVE_ACCEPTANCE.md) provides deterministic SDR test images, a local ReShade/GPU capture plan, compiler-log provenance requirements, a strict evidence validator and adversarial validator tests. Run:

```bash
python -m native_acceptance probe
python -m native_acceptance prepare --output ../native-run-local
python -m native_acceptance verify --bundle ../native-run-local
```

The first two commands prepare a plan and inspect tool discovery; **the final command must fail on an unfilled template**. A completed, hash-consistent record can be marked **evidence ready for independent review**, never automatically GPU-certified. **No ReShade FX compiler or GPU backend has been executed in this development environment**. Keep real diagnostic logs, captures, hardware metadata and other local test artifacts out of GitHub.

## Repository map

```text
transmigrated-FlexAgX/
├── reference/FlexAgX_1.2.fx          Original immutable FX 1.2 reference
├── shader/FlexAgX_transmigrated.fx  Staged corrected FX candidate
├── correction_api/                  Pure probe modules and API glue
├── harness/                         Oracles, bounded runner, archived summaries
├── native_acceptance/               Native fixtures, probe and evidence validator
├── tests/                           Source and API regression tests
├── docs/                            Correction contracts, ledger, source diffs and sync status
├── logs/                            Current TODO, roadmap and historical notes
├── VERIFICATION_REPORT.md           Recorded v0.6.0 verification
├── MANIFEST.json                    Recomputed file integrity inventory
└── SHA256SUMS.txt                   Matching digest ledger
```

## Open risks and release constraints

1. **F18/F32:** native first frame, disable/re-enable, effect reload, resource initialization and synchronization barriers require GPU verification.
2. **F23/F24/F29/F39:** source-level correction strategies await Operator behavioral decisions and target-runtime acceptance.
3. **F30/F31:** negative/superwhite transfer inputs and valid encoded-domain behavior remain unresolved.
4. **F36/F40:** zero-strength tracking and output-conversion continuity remain explicit policy holds. F40 retains exact encoded passthrough at 0%, so a cross-encoding discontinuity can remain.
5. **F19 / native runtime:** ReShade FX compilation, graphics APIs/drivers, float32 fidelity and rendered-pixel comparisons are untested.
6. **Expansion:** independently replaceable full rendering stages, external API exposure and production operations are not authorized by this work.

Consult [canonical TODO](logs/TODO.md), [roadmap](logs/ROADMAP.md), and [repository synchronization record](docs/REPOSITORY_SYNC.md). The project repository is public: contributor and GitHub commit metadata are not anonymous. Do not commit session images, credentials, local SQLite stores, crash dumps or unredacted logs.

**Production gate: LOCKED.** All work stays staged; no merge, deployment or shader-release approval is inferred.

## CT-008: native warning follow-up (v0.8.0)

The first operator-supplied ReShade log reports successful compilation **with warnings**: X4000 ×19 and X3571 ×1, in 1.865 seconds. Generated code addresses are not original FX source line numbers. The x3571 source candidate was guarded with an explicit `max(t, 0.0)` around its pow operand; legal UI-range outputs remain mathematically identical. **This is a staged mitigation, not yet a verified warning fix.** X4000 warnings concerning generated `F__FA_*` helper names require new compiler logs and generated shader inspection before corrective source edits.

To summarize a new native compiler log without publishing local paths/pointers:

```bash
python -m native_acceptance.compiler_warnings --input compiler-local.log --output warning-summary.json
```

See [CT-008 warning triage](docs/CT008_NATIVE_WARNING_TRIAGE.md). Do not publish raw log paths, GPU captures, or driver metadata without review.
