# Transaction integrity v0.5.0 — contract, tests and exclusions

**Status:** STAGED, production gate LOCKED; not a multi-node distributed database.

## Identity and sequencing

Wire request key: `(session_id, frame_index)`. Request fingerprint is SHA-256 over the canonical JSON of all `FrameRequest` fields, including image and settings; it is an idempotency fingerprint, **not authentication**. Exact same key/fingerprint after commit returns the original stored `FrameResult`. Same key/different fingerprint: HTTP 409. Lower index than prior successful journaled frame: HTTP 409. New, higher index: eligible for preparation. Bypass is journaled without temporal exposure advancement.

## Atomicity

1. Preflight controller receipt lookup (before rendering).
2. Observe; prepare provisional state (bounded TTL).
3. Render.
4. Finalize commits response receipt and state together in SQLite `BEGIN IMMEDIATE` transaction.
5. On lost HTTP acknowledgement, read the receipt once; return the stored response only if identity matches. Otherwise fail closed, and retry *the same request*.

The controller should be deployed as **one process** using `FLEXAGX_STATE_DB=/state/controller.sqlite3` or another writable local volume. The default is in-memory test mode. Competing controller processes, multi-node consensus, checkpoint/corruption recovery, authentication and durability under catastrophic disk failure are OUT OF SCOPE.

## Failure semantics

| Trigger | Contract |
| --- | --- |
| Exact retry | Return original response without second temporal step |
| Different payload, same index | HTTP 409 conflict |
| Reordered/old frame | HTTP 409 conflict; no state change |
| Renderer error before finalize | Abort provisional state; retry permitted |
| Crash before finalize | No committed transaction; in-memory prepare discarded |
| Crash after finalize | Receipt persisted and returned after restart |
| Lost finalize ACK | One bounded receipt lookup; unresolved remote loss fails closed |
| Stale receipt evicted | Reject rather than recompute |
| Duplicate bypass frame | Return journaled identity result |

## Bounds and exclusions

512 receipts maximum and 128 MiB budget for serialized receipts. Each receipt limited to 20 MiB. SQLite files require external filesystem quota and backup policy. SQLite transactions are for local controller-process persistence only. The research compatibility endpoints `/v1/control/step` and `/v1/control/commit` remain unsequenced and MUST NOT be used for secure external ingress. No network exposure permitted.

## Source reference and historical evidence

Original upstream shader by El-Greco1541, MIT. `reference/FlexAgX_original.fx` is unchanged. Historical v0.4 results are baseline context, not results of a v0.5 run. All checks must be run locally for this revision.

## Live fault verification

`tests/distributed_v05.py` exercises the five-service path, persistent restart, conflicting duplicate and renderer-down recovery. `tests/ackdrop_v05.py` uses a local forwarding proxy which commits a frame and then deliberately drops its successful HTTP acknowledgement, verifying that the gateway resolves the durable receipt and does not apply the frame twice. These tests do not imply WAN or multi-controller certification.
