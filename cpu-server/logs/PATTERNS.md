# Patterns / lessons / anti-patterns — R4

- Pattern: each phase must have a fresh evidence namespace, verifiable metadata, unique cases and an independently checked exit status.
- Pattern: negative testing includes testing the test mechanism itself, using deliberate timeouts and poisoned evidence.
- Pattern: application integrity is a whole-source hash set, not just a preserved shader digest.
- Pattern: distinguish suite counts from individual stress frames and from nested distributed subchecks.
- Anti-pattern corrected: retaining process output in an unbounded temporary file while calling it bounded because only the displayed tail was capped.
- Anti-pattern corrected: trusting a pre-existing evidence file or a declared `passed` count without inspecting actual case statuses.
- Anti-pattern corrected: fixed service ports without checking the health endpoint's declared service identity.
- Unresolved anti-pattern (application): distributed commits lack durable, idempotent acknowledgement recovery.
