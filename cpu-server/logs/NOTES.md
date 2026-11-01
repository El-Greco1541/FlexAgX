# Research notes — R4 / 2026-11-01

**Scope:** Harden test harness, run application assurance pass, structured fuzz pass and torture test. All work staged locally under production lock.

The inherited v0.3 harness had several assurance weaknesses: it could consume an old phase-result file, parse metadata without reconciling actual case records, capture output in an unbounded temporary file, and count a distributed script as one aggregate check. A prior CLI-validation ordering flaw permitted tests to begin before rejecting an illegal frame-count argument. The updated harness closes those weaknesses, adds test-harness fault injection and a seedable cross-service fuzz suite, and verifies pinned application source hashes before and after execution.

Final complete campaign: 1040 counted checks, 1040 passed, 0 failed. Independent maximum-size 1000-frame torture: 5/5 suites passed. Two earlier 1000-frame campaigns passed before final harness accounting changes. The original `.fx` shader and all `flexagx/` and `services/` Python modules match the unchanged v0.3.0 source.

**No new application failure** was observed. This does not imply application correctness outside tested domains. Real ReShade GPU execution and compiler conformance remain open.

## 2026-11-01 — v0.5.0 transaction research

Implemented request fingerprint + frame-index high-water mark, bounded exact-response receipts, SQLite atomic state/response commit, replay after restart, bypass journaling, and bounded recovery after lost finalize acknowledgments. Added 9 dedicated regression/fuzz scenarios, eight live distributed restart checks and three live acknowledgment-loss proxy checks; all included in the final 1,060-check campaign. Source and original shader hashes checked. No upstream, main-branch, or production modification authorized.
