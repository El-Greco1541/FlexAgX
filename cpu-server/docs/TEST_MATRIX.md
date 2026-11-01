# Test Matrix and Evidence Accounting

| Category | Count in final 20261108 campaign | Coverage |
|---|---:|---|
| Structural static audit | 1 | AST bounds, initialized fields, finite/wire constraints |
| Harness fault-injection selftest | 1 | Timeout, log flood, stale/poisoned evidence |
| Application regression | 44 | Existing API/state regressions |
| Existing validation fuzz | 333 | Malformed payloads, extreme numbers, limits |
| Mathematical/image metamorphic | 85 | Output, histogram, LUT and alpha properties |
| Expanded adversarial fuzz | 567 | All five endpoints, duplicate/nonfinite JSON, transaction limits |
| Torture suite | 5 | Frame loop, size limits, session capacity, concurrency |
| Distributed checks | 4 | Five servers, successful frame, renderer loss, rollback |
| **Total** | **1040** | **All passed** |

The final full-harness run uses seed 20261108 and 350 sequential torture frames; the separate maximum-size torture artifact uses seed 20261106 and 1000 frames. Two earlier complete 1000-frame campaigns with seeds 20261102 and 20261103 also passed (1,037 counted checks each, before the distributed accounting was expanded to four separate cases). Thus 1040 refers to the final full run, not an invented aggregation of all stress-frame requests. Each torture suite has one aggregate result for its frame loop, not a per-frame counted check.

**Outcome:** All observed checks passed; zero observed new application failures. The result is not a guarantee of correctness or production readiness.

Evidence: `results_v04/RUN_REPORT_FINAL_20261108.json`, `results_v04/TORTURE_1000_20261106.json`, `results_v04/RUN_REPORT_20261102.json`, `results_v04/RUN_REPORT_20261103.json`; complete case-level records under `results_v04/runs`.
