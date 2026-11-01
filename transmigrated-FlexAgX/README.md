# Transmigrated FlexAgX — correction-first shader development

**Status: STAGED RESEARCH · Phase 1: CORRECT FIRST · F39 candidate v0.6.0 · Expansion: NOT YET AUTHORIZED**

This independent workspace starts with the original **FlexAgX 1.2** by **El-Greco1541** (MIT licensed), uses the existing 43-finding audit and prior CPU-server architecture as research inputs, and makes narrowly documented shader corrections before expanding behavior. It does **not** replace, edit or claim upstream authorship for the original shader.

## What changed in v0.1.0

| Change | Finding | Why |
|---|---|---|
| Explicit conditional hue-angle guards in both P4 and P8 | F38 | Avoid invoking `atan2(0,0)` for achromatic pixels where the shader-language result is undefined |
| Extra initial histogram-zeroing pass (P0) before P1 | F41 | Prevent first-use histogram atomic accumulation on uninitialized counters at the source-pass level |

This is an intentional **9-pass FX candidate**: one correction preclear pass plus the original eight passes. **F41 GPU/runtime verification remains pending**, and CT-003 introduces defensive temporal marker validation and finite initialization for the persistent state and previous histogram, with native backend acceptance still pending. Source edits are documented in [the correction ledger](docs/CORRECTION_LEDGER.md).

## Workspace

```text
transmigrated-FlexAgX/
├── reference/FlexAgX_1.2.fx             Original, byte-identical (read-only)
├── shader/FlexAgX_transmigrated.fx     Modified correction candidate
├── correction_api/                     Pure correction modules + strict API glue
├── tests/                              Static FX + HTTP + seeded property checks
├── docs/                               Source ledger, architecture, open decisions
├── logs/                               Notes, TODO, errors, agenda and roadmap
├── requirements*.txt                   Development dependencies
└── VERIFICATION_REPORT.md              Local test evidence
```

### Source provenance

- Original: [El-Greco1541/FlexAgX](https://github.com/El-Greco1541/FlexAgX), release 1.2.
- Root fork [MIT LICENSE](../LICENSE) retains the original copyright and license notice.
- Original SHA-256: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- Current corrected candidate SHA-256: `6603e5ecb42458ce55845021d56c653ed01806ecaead3a5be21c69b6152808ca`.
- The old `cpu-server/` and `code-transmigration/` workspaces remain unchanged. This is a separate staging branch.

## Run local correction probes (not a renderer)

From this directory with Python 3.10+:

```bash
python -m pip install -r requirements-dev.txt
python -m uvicorn correction_api.api:app --host 127.0.0.1 --port 8081
```

Endpoints: `GET /health`, `GET /v1/capabilities`, `POST /v1/correction/hue` and `POST /v1/correction/histogram`. The probe interface is deliberately **not** a full-frame shader API. It validates corrected mathematical boundaries and testable module contracts only. For actual CPU image processing, see the existing `cpu-server/` workspace and its separate v0.5 journal.

Example achromatic hue request:

```json
{"stage":"output-gamut","a":0.0,"b":0.0}
```

Response is a finite sentinel with angle zero and reason `ACHROMATIC_FALLBACK`. Histogram requests require exactly 64 integer bins plus matching valid/white/sample counters. Each call starts from an explicit 67-slot zero state. Any invalid wire input receives a typed rejection sentinel and no mutation. All computation ports are replaceable and no concurrent persistent state is exposed by the probe service.

## Hardened effect harness (v0.2.0)

The new [effect-harness guide](docs/EFFECT_HARNESS.md) covers isolated test processes, fail-closed evidence validation, original-vs-candidate source hashing, deliberate shader-regression mutations, hue/histogram reference oracles, adversarial JSON, 8-thread live HTTP, and **1,000-/2,000-frame synthetic sampling torture**.

**Result:** Two campaigns passed **24,138 counted checks cumulatively**, with **40/40 pytest tests**. This verifies only CPU correction probes and source properties—not actual `.fx` rendering. No ReShade FX compiler or GPU runtime was available, and `FA_State`/`FA_HistPrev` first-use and backend barrier semantics remain unverified. See [Verification](VERIFICATION_REPORT.md).

```bash
python -m pytest -q tests
python -m harness.selftest
python -m harness.runner --seed 20261101 --frames 1000
python -m harness.runner --seed 731234 --frames 2000
```

## Test

```bash
python -m pytest -q tests
```

The suite validates reference immutability, source edit locations, preserved original pass order, hue origins, 256 seeded hue probes, 256 seeded histograms, HTTP errors, bounds and module injection. **These are CPU/static tests, not a ReShade compiler or runtime test**. Verify the recorded results in [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

## Correctness-first release conditions

Before adding color features, more API servers or GPU glue, resolve the behavior decisions in [PENDING_DECISIONS](docs/PENDING_DECISIONS.md). Highest outstanding risks are **FA_State/FA_HistPrev native cold-start/reload acceptance**, GPU compiler acceptance, and **F39/F40 gamut/encoding behavior**. Do not substitute visual opinions or throughput measurements for reproducible contracts.

**Do not expose the probe API beyond localhost.** The public fork is not anonymous at GitHub-account level. Upstream MIT attribution is retained. This package contains no authorization to merge, deploy, publish a shader release or clear the project production gate.

## v0.3.0 — F18/F32 cold-start correction (staged)

CT-003 adds a validated `FA_TemporalBoot` record to the shader state pass. A missing or discontinuous marker causes finite controller defaults and a current-histogram first-frame baseline. It does not add any passes, alter the upstream shader, or deploy a backend. See [Temporal boot correction](docs/TEMPORAL_BOOT_V03.md) for exact limits and the GPU acceptance matrix.

**Updated verification:** 48/48 pytest and 40,366/40,366 cumulative static, CPU, adversarial and simulated-frame checks across two completed campaigns. No real ReShade rendering or FX compilation was performed. The older v0.2 evidence is historical and not a claim of v0.3 GPU parity.

## v0.4.0 — F23/F24 deadband settling (staged)

The corrected S5 step now stops residual scene-key velocity when the exposure-key error is within the configured inclusive deadband. Outside the deadband, the original source equations remain unchanged. This is a **proposed correctness contract**, not a GPU-certified fix or an Operator-approved policy change. See [CT-004 contract](docs/CT004_DEADBAND_SETTLING.md) and [source diff](docs/CT004_SOURCE_DIFF.patch).

**New validation:** 79/79 pytest; 55,570/55,570 cumulative checks across two fully completed CPU/static harness campaigns (1,000 and 2,000 simulated frames). There has been **no** native ReShade compilation or GPU execution. F29/F36 diagnostic holdouts and F39/F40 color policy remain open. Production gate LOCKED.

## v0.5.0 — F29 two-observation scene-cut confirmation (staged)

CT-005 requires a prior discrepant frame before confirming a scene cut. A single slow/stalled frame cannot trigger an exposure scene-cut correction merely because clamped `dt` exceeds 100 ms. The existing histogram distance calculation, persistence threshold and rate-limited applied exposure are unchanged. This is a narrowly staged correctness candidate, not a certified GPU fix; [CT-005 contract](docs/CT005_SCENE_CUT_CONFIRMATION.md) and [source diff](docs/CT005_SOURCE_DIFF.patch) document it.

**Verification:** 100/100 pytest, 16/16 harness self-tests, and two completed campaigns totaling 107,000/107,000 CPU/static checks (seeds 20261101 and 731234, 3,000 synthetic frames). F36 internal tracking at 0% automatic exposure is deliberately preserved. Original shader remains immutable (SHA-256 `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`). Real ReShade compilation, GPU rendering and Operator behavioral acceptance remain outstanding. Production gate LOCKED.

## v0.6.0 — F39 post-blend gamut guard; F40 explicit policy hold

The new `FA_ConstrainGamutAfterMix` stage runs **only for out-of-gamut
composites after** the original white-balanced/processed strength blend.
Already in-gamut values are unchanged; outliers are bounded through a
12-iteration Oklab constant-lightness chroma search rather than routine
RGB hard clipping. The original pass order remains **nine** (including P0
histogram preclear); all earlier exposure/scene-cut corrections remain.

**F40 has not been behaviorally repaired.** The exact 0%-strength encoded
bypass remains in place, even when output encoding differs from input.
A near-zero discontinuity is therefore possible and has tests, not a new
policy. See [CT-006/F39-F40 contract](docs/CT006_F39_GAMUT_AND_F40_ENCODING.md).

**v0.6.0 verified locally:** 113/113 pytest tests, 16/16 harness self-tests,
and 125,545/125,545 counted checks across two process-isolated campaigns
(1,000 and 2,000 simulated frames). This is not ReShade compiler acceptance,
a GPU test, nor an approved visual correction. See `VERIFICATION_REPORT.md`.

`python -m harness.runner --seed 20261101 --frames 1000`

**Gate:** remain staged; do not merge or deploy without explicit Operator clearance.
