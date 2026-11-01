# R4 Verification Report

**Date:** 2026-11-01  
**Scope:** staged CPU API/harness; production locked  
**Result:** PASS — 1040/1040 counted checks

| Test phase | Checks | Passed | Failed | Duration (s) |
|---|---:|---:|---:|---:|
| static_audit | 1 | 1 | 0 | 1.319 |
| harness_selftest | 1 | 1 | 0 | 3.725 |
| regression_and_assurance | 44 | 44 | 0 | 3.127 |
| validation | 333 | 333 | 0 | 2.575 |
| metamorphic | 85 | 85 | 0 | 1.820 |
| adversarial | 567 | 567 | 0 | 2.821 |
| torture | 5 | 5 | 0 | 7.156 |
| distributed_guarded | 4 | 4 | 0 | 4.882 |

The final full run used **350 sequential torture frames** (seed `20261108`). A separate reproducible maximum-size **1000-frame torture run** (seed `20261106`) passed 5/5 suites. Full 1000-frame runs at seeds `20261102` and `20261103` also passed before the final four-check distributed accounting was added.

## What was tested

Input and structural fuzz, mathematical/image invariants, boundedness and controller state, process-failure containment, source integrity, real localhost five-server rollback, output/evidence null exclusion, and harness self-fault injection.

## What remains unverified

Actual GPU/ReShade operation, production-grade durability, authentication, WAN failures, total termination proof for native libraries, production performance and pixel identity. No previously reported shader defect is marked resolved.
