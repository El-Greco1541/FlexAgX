# R4 Hardening Pass — Harness and Evidence Pipeline

**Status:** Staged; not deployed. **Application:** unchanged from v0.3.0. **Reference shader:** byte-identical. **Research date:** 2026-11-01.

## Controls strengthened

1. Every run uses a fresh unpredictable run directory, preventing stale evidence from being silently reused.
2. Every phase's output is strictly checked for expected phase and seed, finite JSON numbers, non-null values, matching case counts, unique case names, declared status consistency, size, and bounded nesting.
3. Child processes have watchdog deadlines, bounded captured output, subprocess-group termination (POSIX), and bounded process-output tails; Windows uses a best-effort taskkill-tree fallback.
4. Source integrity is verified against a pinned shader digest and a separate 20-file application/reference SHA-256 baseline before and after a campaign.
5. Harness itself executes deliberate timeout, output-overflow, evidence-poisoning and source-integrity self-tests.
6. CLI frame and seed limits are validated before test execution. The suite runner's control and stream-reading loops are explicitly bounded; the structural audit scans harness files as well as application files.
7. Distributed tests allocate ephemeral localhost ports and record four separate cases in machine-readable, non-null evidence. A killed renderer must return a failure and leave controller state unchanged.
8. Fuzz corpus covers all five service interfaces, malformed/non-finite/duplicate JSON, contradictory types, and state prepare/commit/abort and pending capacity.

## Explicit bounds

- Harness frames per campaign: 1..1000.
- Subprocess duration per phase: 1..180 seconds (individual suites have stricter limits).
- Captured subprocess output budget: 1,048,576 bytes; retained tail: 12,288 bytes.
- Evidence file budget: 8,000,000 bytes; case records per phase: 4,096; JSON nesting depth: 32.
- External application requests retain v0.3 caps: 21 million request bytes, 2 million image pixels, 1,024 LUT samples, 128 sessions and 128 pending transactions.

## Fallbacks

- Invalid or missing evidence: fail the associated phase, not an implicit pass.
- Invalid numeric payloads: application responds with typed INVALID or LIMIT_EXCEEDED sentinel responses where the relevant endpoint supports it.
- Timeout, excessive output, or orphaned subprocess pipe: kill subprocess group, fail the phase.
- Unexpected renderer outage: gateway rejects the frame; controller provisional state is aborted/expired.
- Integrity mismatch: stop before executing tests or report a failed campaign.

## Residual limits

Static AST checks are not a termination proof; C/NumPy/Pillow native operations are not covered by per-call time limits within a live server. No authenticated production deployment, durable transaction log, GPU equivalence, WAN fault simulation, or exhaustive coverage is established. The Windows process-tree fallback has not been executed in this environment. Source-preserving tests do not repair F01–F43 shader findings. No changes were made to the service implementation.
