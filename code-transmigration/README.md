# FlexAgX — Code Transmigration

**Correctness-first translation workspace | version 0.1.0 | staged research only**

This directory is a separate engineering workspace for translating the original **FlexAgX 1.2 ReShade FX** shader into modular, observable CPU services coordinated by explicit **API contracts and orchestration glue**. We deliberately prioritize **correctness, auditability, bounded failure, reproducibility, and interchangeable modules over speed**.

> **Not production software.** This work is neither a ReShade add-on nor a GPU implementation. CPU output is an approximation and has not been certified for pixel-level or float-level equivalence. No launch, merge into `main`, remote network exposure, or production-gate clearance is implied.

## 1. Source and intellectual provenance

- Original shader author: [El-Greco1541 / FlexAgX](https://github.com/El-Greco1541/FlexAgX), **MIT** license, release [1.2](https://github.com/El-Greco1541/FlexAgX/releases/tag/1.2).
- An **unaltered 49,502-byte source copy** is retained at [`reference/FlexAgX_1.2.fx`](reference/FlexAgX_1.2.fx). SHA-256: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- The fork's root `LICENSE` retains the upstream copyright and MIT notice. This rendition is independently maintained research; no upstream endorsement or transfer of authorship is implied.
- Earlier source-audit methodology was intentionally obscured; source locations, contracts, test conditions, results, and uncertainties remain disclosed.

## 2. Design principle: correctness is the constraint

Every module must have an explicit input, output, owner, version and failure state. A failed computation cannot silently advance exposure state. Undefined or missing values are **typed sentinels** or **rejected input**, never JSON `null`. No silent normalization of invalid inputs. No unbounded retry loops. Mathematical approximations are described, not hidden as source-equivalent results.

As a deliberate first stage, this workspace **reuses the tested v0.5.0 CPU numerical foundation** in the sibling [`../cpu-server/`](../cpu-server/) directory through replaceable ports. It does not copy and independently mutate those equations; this reduces the number of divergent implementations while pass-level APIs and conformance fixtures are developed.

### Architecture

```text
             ReShade FX 1.2 — immutable source reference
                            |
                     eight-pass map
                            |
                    v1 HTTP contracts
                            |
                 +----------v---------+
                 | Correctness-first   |
                 | sequential GLUE     |
                 +--+----+----+----+---+
                    |    |    |    |
            +-------+    |    |    +--------------+
            |            |    |                   |
        Observer     Controller/State          Renderer
        histogram    prepare / finalize        CPU pixels
            |            |    ^                   ^
            |            v    |                   |
            +---------- Tone / LUT --------------+
                     transactional response
                            |
                   Output + state receipt
```

**Module responsibilities:**

| API boundary | Source pass coverage | Implementation today | Confidence |
|---|---|---|---|
| Observation | P1 histogram | CPU histogram and phase sampling | Tested CPU equations, not runtime parity |
| Controller | P2 state | v0.5 SessionStore, serialized preparation and SQLite receipt | Tested local transactional behavior |
| Tone synthesis | P2 LUT logic | v0.5 1,024-entry LUT builder and validation | CPU numerical checks |
| Render | P3–P8 curve, hue, detail and final encoding | v0.5 grouped CPU renderer | **Grouped approximation**, not independent pass emulation |
| Glue | Across all stages | New serial coordinator with bounded error paths | Tested local behavior |

The public module map reports all eight original pass names and the current aggregation of implementations. It **does not** imply a one-to-one CPU/GPU resource allocation or per-pass float16 render-target equivalence. See [source mapping](docs/SOURCE_MAP.md) and [boundaries](docs/BOUNDARIES.md).

## 3. New workspace structure

```text
code-transmigration/
├── README.md
├── reference/FlexAgX_1.2.fx       Immutable upstream FX source
├── transmigration/
│   ├── dependencies.py             Fail-closed sibling and source integrity checks
│   ├── modules.py                  Immutable eight-pass catalog and ownership
│   ├── adapters.py                 Replaceable observer/tone/renderer/image ports
│   ├── glue.py                     Correctness-first transactional orchestration
│   └── api.py                      Local-only modular HTTP facade
├── tests/test_correctness.py       Reproducible source, API and state tests
├── docs/SOURCE_MAP.md             FX-to-service traceability
├── docs/BOUNDARIES.md             Fidelity, limitations and decision record
├── logs/TODO.md                   Next engineering work
├── logs/ERROR_LOG.md              Open issues and evidence gaps
└── requirements*.txt              Dependencies from sibling CPU baseline
```

## 4. Running the local API

From this folder, with **Python 3.10+** and the sibling `cpu-server/` still available:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn transmigration.api:app --host 127.0.0.1 --port 8090
```

Open <http://127.0.0.1:8090/docs>. The facade exposes:

- `GET /health` — status, version, locked production gate.
- `GET /v1/modules` — original pass ordering, module ownership and fidelity labels.
- `GET /v1/provenance` — immutable upstream source hash and license.
- `POST /v1/frame` — strict frame contract, sequential CPU rendering, durable receipt/replay when configured.

Use the pre-existing [`../cpu-server/docs/API_CONTRACT.md`](../cpu-server/docs/API_CONTRACT.md) for the full validated request schema. The new facade **does not** expose the older unsafe direct control-step or commit endpoints. This v0.1 release intentionally keeps the numerical ports local; network-distributed port adapters are a separate validation milestone, not an undocumented shortcut.

By default temporal receipts are in memory. To persist a journal across restarts, set `FLEXAGX_TRANSMIGRATION_DB` to a writable local SQLite file **before starting the service**. No secrets or real-image journal files belong in Git. Persistence supports one controller process, not replica consensus.

## 5. Test and reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Tests cover upstream source hash and eight-pass map; legal image processing; JSON no-null API behavior; deterministic replay, stale/conflicting frame rejection; zero-strength bypass; local SQLite restart recovery; and failure rollback when the renderer raises. The evidence file in this folder describes only tests actually executed against this rendition. Legacy CPU v0.5.0 tests remain in the sibling project.

## 6. Known limitations and explicit next steps

1. The renderer still groups P3–P8. **Next:** split them into explicit typed intermediate passes, preserve original intermediate semantics, and validate each decomposition against the existing baseline before adopting it.
2. A CPU image in PNG/RGBA8 is not a GPU scene-linear HDR framebuffer. FX precision, texture sampling, exposure first-use behavior, Oklab achromatic handling and transfer-function boundaries require independent verification.
3. API transport is presently a local, in-process modular adapter. Authenticated, individually deployed microserver adapters are **future work** requiring reproducible conformance tests and strong transaction recovery.
4. No authentication, TLS, remote service identity, Windows/Docker validation, native resource isolation or GPU compiler/backend certification is included.
5. Reference findings F01–F43 remain open unless separately dispositioned. A passing CPU test does **not** resolve them.

The objective is not high FPS. The objective is a **defensible, modular, functional rendition whose limitations and evidence can be audited**.

## 7. Publication and control

This is a public fork. The source and artifacts are screened for private host paths, personal profiles and secrets; GitHub ownership/commit information remains public. Required MIT attribution is retained. **Production gate: LOCKED.** Changes belong on a reviewable staging branch; no deployment or promotion is authorized.
