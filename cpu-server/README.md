# FlexAgX CPU Server Simulation

**Experimental CPU reconstruction of FlexAgX as a versioned HTTP API, five local microservices, and reproducible test infrastructure.**

> **STAGED DEVELOPMENT — NOT A RESHADE PLUGIN, GPU IMPLEMENTATION, OR PRODUCTION SERVER.**
> Production gate: **LOCKED**. Only a separately authorized operator release may change this status.

This project is deliberately housed in `cpu-server/`, separate from the upstream ReShade FX shader repository. It preserves the original FX shader as a reference while exploring whether the exposure controller, tone-curve generator, observer, and perceptual rendering operations can be expressed as observable services with explicit contracts.

## Origin, attribution and license

- **Original author / upstream:** [El-Greco1541 — FlexAgX](https://github.com/El-Greco1541/FlexAgX).
- **Upstream version represented:** [FlexAgX 1.2](https://github.com/El-Greco1541/FlexAgX/releases/tag/1.2), asset `FlexAgX_1.2.fx`.
- **Original shader SHA-256:** `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- **License:** MIT. The upstream root `LICENSE` is retained unchanged; original copyright and credit remain with El-Greco1541. The CPU translation and orchestration are derivative research work; no endorsement or upstream authorship is implied.
- **Methodology disclosure:** Source-audit methodology was intentionally obfuscated in earlier research at operator request; source references, known limitations, tests, and reproducibility evidence remain documented.

## What actually runs

```text
                   HTTP POST /v1/frame
                           │
                   ┌───────▼───────┐
                   │  API gateway  │
                   │  port 8080    │
                   └───────┬───────┘
                           │  local in-process OR distributed HTTP
               ┌───────────┼───────────────────────┐
               ▼           ▼           ▼           ▼
           Observer    Controller     Tone       Renderer
           histogram   session &     LUT         gamut, WB,
           / percent.  adaptation   synthesis    detail, output
               └───────────┴───────────┴───────────┘
                           │
                   PNG image + metadata
```

- **Observer:** bounded 64-bin log-luminance histogram, percentile and phase statistics.
- **Controller:** session-scoped temporal adaptation, scene state, provisional `prepare → commit / abort` transaction interface.
- **Tone:** 1,024-point LUT, validation and explicit fallback.
- **Renderer:** CPU NumPy/SciPy approximate rendition of color, detail, and display transformations.
- **Gateway:** JSON contract, image exchange, bounded request handling and cross-service ordering.
- **Clients:** Python, JavaScript and PowerShell examples.
- **Verification:** existing regression, adversarial/seeded fuzz, property tests, stress/torture tests and distributed fault injection.

The modules are independently launchable. **They are a CPU reference/simulation**, not a bridge to a live GPU, ReShade process or HDR framebuffer. The source's RGB and Oklab equations are ported where feasible; float64/float32, texture sampling and intermediate render formats can differ.

## Quick start: local in-process mode

Requirements: Python 3.10+ recommended; install packages in a disposable virtual environment. Use this directory as the working directory.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn services.gateway:app --host 127.0.0.1 --port 8080
```

Browse **http://127.0.0.1:8080/docs** for the generated OpenAPI interface, or `GET /health` and `GET /v1/capabilities` for basic checks. The principal image operation is `POST /v1/frame`; it takes base64-encoded PNG input, a session ID, frame index and optional settings, and returns a PNG plus controller/tone metadata. See [the API contract](docs/API_CONTRACT.md) and [examples/client.py](examples/client.py) for the exact schema.

For an offline image operation without an HTTP server:

```bash
python -m flexagx.cli --help
```

## Five-service local-only mode

```bash
docker compose up --build
```

Compose binds the gateway only to **127.0.0.1:8080**; four internal servers share a container network and are not published. **Docker execution has not been certified in the research environment**. The controller must run with one worker because its session store is process-local. No TLS, auth, rate-limited network perimeter, durable controller store or multi-replica consistency is supplied. Do not expose this service publicly or to untrusted networks.

Manual server commands and environment variables are documented in [Architecture](docs/ARCHITECTURE.md); `GATEWAY_MODE=local` is the default.

## Verify and reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python -m harness.run_sentinel_harness --seed 20261108 --frames 350
python -m harness.phase torture --seed 20261106 --frames 1000 --output results_v04/TORTURE_1000_20261106.json
```

The archived v0.4.0 campaign recorded **1,040/1,040 checks passed**, and an independent **1,000-frame torture run** passed all five suites. A later project-level campaign reported two additional passing seeded runs plus independent HTTP and client checks; see the archived project-test evidence for that separate provenance. **These are historical research results, not a new GitHub CI run or GPU acceptance test.** Re-run on your own platform before drawing deployment conclusions. This repository staging commit does not run Docker or deploy anything.

See [Verification](VERIFICATION_REPORT.md), [Hardening pass](docs/HARDENING_PASS.md), [Test matrix](docs/TEST_MATRIX.md), and [Sentinel/bounds invariants](docs/SENTINEL_BOUNDS_INVARIANTS.md).

## Invariants and deliberate limits

| Concern | Current development contract |
| --- | --- |
| Absent values | Explicit typed sentinel records at tested JSON boundaries; no `null`/NaN/Infinity payload values |
| Initialization | Explicit state defaults and lifecycle checks |
| Workload bounds | Request/image/LUT/session limits, finite validation, bounded iteration and timeouts |
| Failure fallback | Reject invalid input, identity bypass, verified curve fallback, hold or abort provisional updates |
| Controller mutations | Prepare/commit/abort prevents a subset of partial state commits |
| Source provenance | Original ReShade FX reference remains byte-identical and hash-pinned |
| Publication | Research code only; no production enablement |

**Open blockers:** there is no authenticated external access; per-frame idempotency/replay suppression is missing; sessions live only in RAM; distributed acknowledgments can become ambiguous after network failures; floating-point parity with ReShade has not been established; production resource budgets and dependency hardening remain open. These are documented rather than silently “fixed.”

## Directory guide

```text
cpu-server/
├── README.md              ← this document
├── flexagx/               ← CPU numerical kernels, contracts, session logic, CLI
├── services/              ← gateway, observer, controller, tone and renderer
├── clients/               ← JavaScript + PowerShell
├── examples/              ← Python client
├── harness/               ← bounded seeded fuzz/torture/self-test runner
├── tests/                 ← regressions and distributed fault probes
├── docs/                  ← architecture, API, invariants, research matrix
├── reference/             ← original unmodified FX source and baseline hashes
├── results_v04/           ← selected historical summary evidence
├── logs/                  ← lessons, TODO, error log and roadmap
├── compose.yaml           ← optional local-only topology
├── Dockerfile             ← local research image
└── SHA256SUMS.txt         ← staged file integrity ledger
```

## Publication/privacy boundary

Research-source materials have been screened to avoid identifiable local workspace paths, private account data, credentials and personal log metadata. The upstream author’s legally required MIT attribution is retained. **This public fork and its Git commit metadata are not anonymous.** See [Publication and privacy audit](docs/PUBLICATION_PRIVACY.md).

## Publication/privacy boundary

Research-source materials have been screened to avoid identifiable local workspace paths, private account data, credentials and personal log metadata. The upstream author’s legally required MIT attribution is retained. **This public fork and its Git commit metadata are not anonymous.** See [Publication and privacy audit](docs/PUBLICATION_PRIVACY.md).

## Change and release policy

The upstream fork's root `README.md` and `LICENSE` are not overwritten. CPU code and its tests live entirely in this directory. New work should enter through a **reviewable staging branch**, be validated against the pinned reference, and receive explicit operator clearance before any merge, production deployment or externally reachable exposure.

**Upstream shader:** © 2026 El-Greco1541, MIT. **CPU-server staging:** experimental, independently maintained research adaptation.
