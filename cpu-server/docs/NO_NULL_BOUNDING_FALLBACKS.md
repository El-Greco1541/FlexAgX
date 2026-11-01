# FlexAgX v0.3.0 — Sentinel and Bounded-Execution Contract

**Release status:** staged local research artifact; no production promotion or shader modification.

## Rule S0 — No JSON null

- Any missing, inapplicable, absent, or unavailable **wire value** is represented by a typed sentinel:
  `{"kind":"NOT_APPLICABLE","reason":"bypassed frame","fallback":"IDENTITY"}`.
- Allowed `kind` values: `NOT_APPLICABLE`, `UNAVAILABLE`, `UNINITIALIZED`, `INVALID`, `NOT_FOUND`, `EXPIRED`, `CONFLICT`, `UPSTREAM_FAILURE`, `LIMIT_EXCEEDED`.
- Allowed fallback values: `IDENTITY`, `REJECT`, `HOLD`, `RETRY_EXPLICIT`, `SKIP`.
- Required fields may not be replaced by sentinels: invalid inputs are rejected with a 4xx error whose body contains a structured sentinel. This is not equivalent to silently substituting a default.
- All FastAPI request/response Pydantic contracts disallow nonfinite floats and unknown fields. No nullable response fields remain.
- Null and nonfinite values deliberately injected by negative fuzz tests **must be rejected**, not returned or persisted.
- The old source `.fx` file is preserved as a historical reference and is outside the migrated JSON-wire guarantee.

## Rule S1 — Explicit initialization

- `State` has explicit defaults for scene key, velocity, knee, timer, stored strength, initialized flag, applied EV, warmup, histogram, frame count and lifecycle.
- Lifecycle begins `UNINITIALIZED`; inactive but previously initialized state is `HOLD`; adaptation sets `ACTIVE`.
- Frame gateway initializes `token` with empty-string no-token marker; each required wire field is either supplied, defaulted with a finite value, or rejected.
- Uninitialized control structures are never silently represented as JSON null.

## Rule S2 — Quantitative bounds

| Resource or loop | Upper bound | Enforcement |
|---|---:|---|
| HTTP request size | 21,000,000 bytes | ASGI request-size guard (including streamed bodies) |
| Base64 image field | 20,000,000 characters | Pydantic and pre-decode check |
| Decoded image | 2,000,000 pixels | Pillow check and explicit multiplication |
| Histogram bins | 64 | Exact-length contract |
| LUT entries | 1,024 | Exact-length contract and finite monotonicity check |
| LUT attempts | 4 | Fixed `range(4)` |
| Gray-reference search | 30 | Fixed `range(30)` |
| Perceptual gamut search | 10 | Fixed `range(10)` |
| Sessions | 128 | SessionStore guarded capacity |
| Pending frames | 128 | SessionStore guarded capacity |
| Pending-frame lifetime | 30 seconds | Monotonic-clock lazy expiration |
| Per-session frame counter | 2^63−1 | Explicit rejection when cap reached |
| Downstream HTTP request | 15 seconds | httpx timeout per operation |
| Aborted transaction cleanup request | 2 seconds | httpx timeout |
| Fuzz/torture harness frame count | 1 to 1,000 | CLI guard |
| Harness subprocess wall limit | 15 to 160 seconds per suite | Subprocess watchdog |
| Harness capture | 8,000 bytes | Bounded output retained in report |

- No `while` loops are present in the migrated application modules as checked by structural AST audit.
- Core loops iterate fixed ranges or bounded collections: histogram(64), LUT(1,024), pending/session tables(128), image pixels(2m), errors(12).
- **Limitation:** This is explicit source-level bounding, not a formal proof that every native library call terminates before an absolute wall-clock deadline. The separate watchdog bounds integration test processes.

## Rule S3 — Named fallback by branch

| Condition | Fallback | Observable status |
|---|---|---|
| OverallStrength=0 and DebugView=0 | Exact encoded PNG passthrough; metadata sentinels | 200, `NOT_APPLICABLE/IDENTITY` |
| Input `null`, NaN, ±Infinity, contradictory histogram, invalid LUT, oversized input | No compute/persist | 422 or 413, `INVALID`/`LIMIT_EXCEEDED` with `REJECT` |
| Unknown session | No synthetic state created | 404, `NOT_FOUND/REJECT` |
| Tone candidate validation fails | Up to 4 retries, native normalized fallback, final validation | 200 if valid; 422 if no candidate qualifies |
| Nonfinite encoded or rendered pixels | Reject frame, no output substitution | 422, `INVALID/REJECT` |
| Local render failure after controller prepare | Abort provisional state; original state unchanged | 422 or structured 500 |
| Distributed renderer or downstream failure | Abort provisional controller token; expire pending token if cleanup cannot reach controller | 502, structured `REJECT` |
| Commit version conflict | Reject rather than overwrite concurrent state | 409, `INVALID/REJECT` |
| Explicit abort | Discard provisional state | `ABORTED` result |
| Unknown/expired commit token | No commit | `EXPIRED` result |
| Invalid gateway mode | Reject, no arbitrary downstream call | 503, structured `REJECT` |

## Residual boundaries

- `POST /v1/control/step` is retained as a **legacy direct endpoint**. It applies controller state immediately, unlike transactional `/prepare`, `/commit`, `/abort`; it must not be used to stage a distributed frame. It remains for backward compatibility.
- Distributed prepare/commit is a bounded **best-effort orchestration protocol**, not a durable distributed transaction. A lost commit acknowledgement can leave uncertainty about whether the controller committed; process restarts can discard in-memory state and tokens.
- Session state is held in process memory only; no restart durability, authentication, global rate limiter, or cross-process consensus is claimed.
- No direct ReShade GPU testing or compiler certification performed.
