# Transmigrated FlexAgX — correction-first shader development

**Status: STAGED RESEARCH · Phase 1: CORRECT FIRST · Harness v0.2.0 · Expansion: NOT YET AUTHORIZED**

This independent workspace starts with the original **FlexAgX 1.2** by **El-Greco1541** (MIT licensed), uses the existing 43-finding audit and prior CPU-server architecture as research inputs, and makes narrowly documented shader corrections before expanding behavior. It does **not** replace, edit or claim upstream authorship for the original shader.

## What changed in v0.1.0

| Change | Finding | Why |
|---|---|---|
| Explicit conditional hue-angle guards in both P4 and P8 | F38 | Avoid invoking `atan2(0,0)` for achromatic pixels where the shader-language result is undefined |
| Extra initial histogram-zeroing pass (P0) before P1 | F41 | Prevent first-use histogram atomic accumulation on uninitialized counters at the source-pass level |

This is an intentional **9-pass FX candidate**: one correction preclear pass plus the original eight passes. **F41 GPU/runtime verification remains pending**, and the persistent exposure state and previous histogram also need separate initialization guarantees. Source edits are documented in [the correction ledger](docs/CORRECTION_LEDGER.md).

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
- Corrected candidate SHA-256: `ff5f38cfc4f21bee6521b62aeb996eba6ed5bedd95c3745de82ac32d9199f3da`.
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

Before adding color features, more API servers or GPU glue, resolve the behavior decisions in [PENDING_DECISIONS](docs/PENDING_DECISIONS.md). Highest outstanding risks are **FA_State/FA_HistPrev cold-start**, GPU compiler acceptance, and **F39/F40 gamut/encoding behavior**. Do not substitute visual opinions or throughput measurements for reproducible contracts.

**Do not expose the probe API beyond localhost.** The public fork is not anonymous at GitHub-account level. Upstream MIT attribution is retained. This package contains no authorization to merge, deploy, publish a shader release or clear the project production gate.
