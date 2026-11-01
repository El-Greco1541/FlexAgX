# FlexAgX CPU Server Simulation

**Version 0.5.0 — experimental CPU reference implementation, versioned HTTP gateway, independently startable services, and transaction-integrity test harness.**

> **Research/staging only.** This is **not** a ReShade plugin, a GPU backend, a production API, or a claim of pixel-identical rendering. The production gate remains **LOCKED**. This public branch is a development artifact, not an authorization to deploy.

The simulation translates selected processing behaviors of **FlexAgX** into inspectable CPU code and service contracts. It is intentionally isolated in `cpu-server/`: the public fork's upstream root `README.md` and `LICENSE` remain unchanged.

## At a glance

| Capability | Current status |
| --- | --- |
| CPU simulation of exposure, tone curve, perceptual color and detail | Implemented; numerical fidelity not certified against ReShade |
| Gateway plus observer, controller, tone and renderer | Implemented, local or HTTP-distributed mode |
| Per-frame duplicate suppression and stale-frame rejection | Implemented for `POST /v1/frame` |
| Atomic controller state and response receipts | SQLite journal, one controller process |
| Restart and lost-finalize-acknowledgment recovery | Tested in bounded local fault scenarios |
| Sentinel validation, bounded inputs and fallback behavior | Implemented at tested boundaries |
| Regression, seeded fuzz, property, torture and distributed fault testing | 1,060/1,060 reported checks for v0.5.0 |
| Authentication, TLS, multi-node consensus and GPU/ReShade integration | **Not implemented / not verified** |

## Provenance and license

The original shader was created by **[El-Greco1541](https://github.com/El-Greco1541/FlexAgX)** and is distributed under the **MIT License**. This independent CPU-server research adaptation does not claim upstream authorship or endorsement.

- Upstream release: [FlexAgX 1.2](https://github.com/El-Greco1541/FlexAgX/releases/tag/1.2), asset `FlexAgX_1.2.fx`.
- Preserved reference: [`reference/FlexAgX_original.fx`](reference/FlexAgX_original.fx).
- Original reference SHA-256: `e744bdb7c410039f6835485c023f242ea399de14b09b3fd13657c02166d06e4d`.
- The upstream MIT copyright and permission notice are retained in the fork's root `LICENSE`.
- The earlier static investigation intentionally withheld its detailed investigative methodology; source references, technical evidence, reproducible checks and stated limitations remain inspectable.

## System layout

~~~text
                       POST /v1/frame
                             |
                     +-------v-------+
                     |  API gateway  |
                     | localhost:8080|
                     +-------+-------+
                             |
             +---------------+----------------+
             |               |                |
        +----v----+     +----v-----+    +-----v----+
        | Observer|     |Controller|    |   Tone   |
        | histogram     | exposure |    | 1,024-pt |
        | statistics    | + state  |    |    LUT   |
        +---------+     +----+-----+    +-----+----+
                             |                |
                             +-------+--------+
                                     |
                               +-----v-----+
                               | Renderer  |
                               | CPU image |
                               | transform |
                               +-----+-----+
                                     |
                           PNG + state metadata
~~~

The gateway can invoke the shared numerical core in-process (`GATEWAY_MODE=local`, default) or orchestrate four internal HTTP microservices (`GATEWAY_MODE=distributed`). The controller owns temporal state; the other computational services are designed around explicit request/response contracts. **Five HTTP server applications exist in total, including the gateway.**

The renderer uses a CPU approximation with NumPy/SciPy. RGB/Oklab processing, texture sampling, float precision, intermediate formats and PNG transport can differ materially from the original GPU shader.

## Quick start — local CPU mode

Use Python **3.10+** and work from the `cpu-server/` directory.

**Linux / macOS**

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn services.gateway:app --host 127.0.0.1 --port 8080
~~~

**Windows PowerShell**

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn services.gateway:app --host 127.0.0.1 --port 8080
~~~

Open [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs) for the API explorer. Basic endpoints are `GET /health` and `GET /v1/capabilities`. For offline processing, run:

~~~bash
python -m flexagx.cli --help
~~~

By default the controller journal is `:memory:` and **does not survive restart**. For local persistence, set `FLEXAGX_STATE_DB` to a writable, private SQLite file **before starting the server**. Create any parent directory beforehand and do not commit the resulting database.

## Distributed local microservices

A development-only Compose topology is included:

~~~bash
docker compose up --build
~~~

Compose exposes **only the gateway** on `127.0.0.1:8080`, uses internal service networking, and gives the controller a named SQLite volume. **The Docker build and Windows/PowerShell client have not been independently certified.** The controller must run with **one worker**; pending operations and synchronization are not safe across controller replicas.

Manual five-process startup and service URLs are documented in [Architecture](docs/ARCHITECTURE.md). **Do not expose the gateway or internal services to the internet or untrusted clients.**

## API overview

`POST /v1/frame` accepts a session ID, strictly sequenced frame index, elapsed frame time, base64 PNG and shader-style settings. For the complete validated schema, consult [API Contract](docs/API_CONTRACT.md) and [`examples/client.py`](examples/client.py).

~~~json
{
  "session_id": "synthetic-session-01",
  "frame_index": 17,
  "dt_ms": 16.667,
  "image_png_base64": "<actual base64-encoded PNG>",
  "settings": {
    "OverallStrength": 100,
    "AutoExposureStrength": 30,
    "ExposureOffset": 0,
    "LocalDetail": 20,
    "InputEncoding": 0,
    "OutputEncoding": 0
  }
}
~~~

The example's image value is a **placeholder**, not a valid image payload. A successful response provides processed PNG data and state/validation metadata. Some metadata differs for bypass mode; all API callers should follow the generated OpenAPI schema rather than infer fields from this illustration.

### Frame integrity in v0.5.0

The public gateway calculates a SHA-256 fingerprint of the canonical frame request and keys journal entries by `(session_id, frame_index)`. **The fingerprint identifies a request; it is not authentication.**

| Condition | Result |
| --- | --- |
| First valid higher-index frame | Process, then finalize state and response receipt together |
| Same index, identical full request | Return previously recorded response; no second state transition |
| Same index, different request | HTTP 409 conflict |
| Older or reordered index | HTTP 409; do not reprocess |
| Receipt evicted for an old index | Reject rather than silently recompute |
| Zero-strength bypass | Record an exact bypass response without advancing exposure adaptation |
| Renderer error before finalize | Abort provisional update; a retry may proceed |
| Controller restarts after finalized commit | Read persisted state/receipt if SQLite file storage was configured |
| Commit succeeds but HTTP acknowledgment is lost | One bounded receipt lookup; if unresolved, fail closed |

Frame gaps are allowed, but backward movement is not. A client should retry an uncertain frame with **the identical request**, not a substituted image, changed settings, or a new frame index. Full semantics and failure cases are specified in [Transaction Integrity v0.5.0](docs/TRANSACTION_INTEGRITY_V05.md).

**Durability limits:** The implementation retains up to **512 replay receipts**, with a **128 MiB serialized receipt budget** and **20 MiB per-receipt limit**. The total SQLite file size is **not physically capped** by these limits; use filesystem quotas and protect stored image responses. A controller outage can leave commit status uncertain. There is **no multi-controller exactly-once guarantee**. Legacy direct `/v1/control/step` and `/v1/control/commit` endpoints bypass the frame receipt journal and are unsafe for untrusted ingress.

## Test and reproduce

From `cpu-server/`, install development dependencies and execute:

~~~bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python -m harness.run_sentinel_harness --seed 20261104 --frames 350
~~~

For the maximum supported sequential torture setting:

~~~bash
python -m harness.run_sentinel_harness --seed 20261104 --frames 1000
~~~

**Recorded v0.5.0 evidence:** [Verification report](VERIFICATION_REPORT.md) reports **1,060/1,060 counted checks passed**, including seeded validation fuzzing, mathematical properties, harness self-tests, controller restart, live five-service fault injection, and lost-finalize-acknowledgment recovery. A 1,000-frame test generated verified PASS evidence; the enclosing command session timed out after the report was written, so that run must not be characterized as a clean wrapper exit. These are **historical local CPU results**, not a current GitHub CI run, platform certification, or GPU equivalence proof.

Additional documentation: [Test Matrix](docs/TEST_MATRIX.md) · [Hardening Pass](docs/HARDENING_PASS.md) · [Sentinel and Bounds](docs/SENTINEL_BOUNDS_INVARIANTS.md) · [Error Log](logs/ERROR_LOG.md).

## Invariants and safety boundaries

- **No JSON nulls at tested contract boundaries:** typed sentinels represent unavailable, invalid and uninitialized values; non-finite numeric payloads are rejected where validated.
- **Explicit initialization:** controller state uses defined defaults and lifecycle checks.
- **Bounded execution:** tested request sizes, images, LUTs, sessions, pending transactions, loops and subprocess timeouts have limits.
- **Fail-closed behavior:** malformed requests, conflicting frames and indeterminate remote commits do not silently advance state.
- **Evidence integrity:** SHA-256 source pins and seeded tests protect the reference and test baselines.

These are **tested engineering properties**, not a formal proof of all native-library termination, privacy, security or numerical correctness.

## Outstanding work

1. Restrict or remove legacy direct controller mutations that bypass the journal.
2. Implement authentication, authorization and service-to-service identity controls before any network exposure.
3. Add persistent-store quota/backup/corruption testing and address ambiguous cross-node commits; one-controller-process constraint remains.
4. Verify Docker, Windows/PowerShell cancellation and resource exhaustion behavior.
5. Establish dependency pinning, security scans and a reproducible GitHub CI workflow.
6. Compile and test the original ReShade FX shader on supported GPU backends; measure CPU/GPU differences and independently disposition source findings F01–F43.

The roadmap is staged only; **no merge, deployment, or production release is authorized by this README**.

## Project map

~~~text
cpu-server/
├── README.md                  This guide
├── flexagx/                   CPU kernels, contracts, journal, CLI
├── services/                  Gateway + four microservices
├── clients/                   JavaScript and PowerShell
├── examples/                  Python client
├── harness/                   Seeded adversarial/torture runner
├── tests/                     Regression and distributed fault tests
├── docs/                      API, architecture, provenance, limitations
├── reference/                 Unmodified upstream FX and pinned hashes
├── results_v04/               Archived earlier test evidence
├── results_v05/               v0.5.0 transaction verification evidence
├── logs/                      TODO, notes, roadmap and errors
├── compose.yaml               Local-only five-service topology
└── VERIFICATION_REPORT.md     Current documented test result
~~~

## Publication, attribution and maintenance

This is a **public** research branch. Authored materials have been screened for private workstation paths, credentials, raw user imagery and identifying test metadata, but a static screen is **not a privacy certification**. GitHub repository ownership, fork lineage and commit author/committer metadata remain public. Keep SQLite journals, real session data, `.env`, virtual environments, crash dumps and generated user-frame artifacts out of Git.

See [Publication/Privacy](docs/PUBLICATION_PRIVACY.md), [Provenance](docs/PROVENANCE.md), and [Staging/Handoff](docs/STAGING_AND_HANDOFF.md). The original copyright and MIT license remain attributed to **El-Greco1541**.

**Status: v0.5.0 staged, upstream preserved, production gate locked.**
