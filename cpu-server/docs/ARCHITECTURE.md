# Architecture — executable system boundaries

## Service ownership

| Service | Input | Output | State | Health |
|---|---|---|---|---|
| gateway | FrameRequest | FrameResult | Local-mode SessionStore only | `/health` |
| observer | ObserveRequest | Observation | none | `/health` |
| controller | ControlRequest | ControlResult | SessionStore in RAM | `/health` |
| tone | ToneRequest | ToneResult | none | `/health` |
| renderer | RenderRequest | RenderResult | none | `/health` |

The gateway implements **synchronous request sequencing** per frame in the order observer → controller → tone → renderer. Cross-service calls use HTTP/JSON. In local mode the same Python computational core executes without network serialization. The image is not stored by the gateway or by the microservers beyond in-flight buffers.

## Resource semantics

- Controller sessions are keyed by caller-supplied `session_id`; maximum 128 active sessions in this experiment, no eviction, disk persistence, or distributed database.
- The controller has one process-wide lock. This serializes updates within that process but does not make multiple replicas safe. Use exactly one worker for the controller.
- A skipped frame (`OverallStrength <= 0` and `DebugView == 0`) is returned unchanged and does not advance the controller. In original ReShade the technique remains scheduled; this API optimizes away unnecessary CPU work.
- Distributed failures after the controller state update are **non-atomic**, and replay may double-advance the scene key and warmup. API users must avoid retrying without a separately designed idempotency protocol.
- The network transport is not appropriate for high-frame-rate images because base64 PNG serialization, HTTP, and CPU NumPy computation are much more expensive than in-GPU rendering.

## Process invocations without Docker

Open five terminals in project directory:

```bash
python -m uvicorn services.observer:app --host 127.0.0.1 --port 19441
python -m uvicorn services.controller:app --host 127.0.0.1 --port 19442 --workers 1
python -m uvicorn services.tone:app --host 127.0.0.1 --port 19443
python -m uvicorn services.renderer:app --host 127.0.0.1 --port 19444
```

In the fifth terminal:

```bash
GATEWAY_MODE=distributed OBSERVER_URL=http://127.0.0.1:19441 CONTROLLER_URL=http://127.0.0.1:19442 TONE_URL=http://127.0.0.1:19443 RENDERER_URL=http://127.0.0.1:19444 python -m uvicorn services.gateway:app --host 127.0.0.1 --port 8080
```

On Windows PowerShell set each `$env:NAME='value'` variable before starting the gateway.

## ReShade relationship

There is no direct call path from this API into ReShade. ReShade shaders execute inside graphics API pipelines; an FX effect cannot be exposed as an HTTP server simply by compiling the `.fx` file. An authenticated, explicitly authorized ReShade add-on or separate GPU capture/processing bridge would be a **future, separately gated project**. No such connector is included.

## v0.5.0 transaction recovery

The single controller process owns a SQLite journal (`sessions` and `receipts`). The gateway performs a read-only receipt check before every frame; a unique candidate undergoes prepare, render and finalize. Finalize persists result and state in one local SQLite transaction; lost acknowledgments are resolved with one bounded read. SQLite file state survives process restarts only when an on-disk path is configured. In-memory tests intentionally do not persist. Do not run multiple controller workers or expose internal endpoints to untrusted traffic.
