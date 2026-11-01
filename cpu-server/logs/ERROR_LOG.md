# Error and limitations ledger — R4

| ID | Observation | Resolution / remaining scope |
|---|---|---|
| H04-01 | Previous runner could reuse stale evidence | Fixed: fresh unique per-run directories; missing files fail closed |
| H04-02 | Child process could generate unbounded output file | Fixed: stream with maximum output budget and capped retained tail |
| H04-03 | Suite exit status could disagree with report counts | Fixed: strict evidence count/status/seed reconciliation |
| H04-04 | Previous harness phase CLI validated limits after running | Fixed: validate before execution |
| H04-05 | Previous distributed smoke used fixed ports and one aggregate check | Fixed: ephemeral ports, four independently recorded checks |
| H04-06 | Initial v0.4 source audit caught unbounded log-tail `while` | Fixed: replaced with explicitly bounded `for` and reran audit |
| H04-07 | Previous code pin covered the shader but not app sources | Fixed: SHA-256 baseline for 20 application/reference files |
| H04-08 | A third 1000-frame full-run command was interrupted before a final report | Not counted as a completed full run; separate complete 1000-frame torture result retained |
| R04-01 | No real ReShade FX compiler or GPU validation | Unresolved runtime boundary |
| R04-02 | CPU native libraries cannot be formally proven time bounded via source AST | Unresolved native backend boundary; harness watchdog contains subprocess tests |
| R04-03 | Windows tree termination fallback has not been tested here | Platform verification needed |
| R04-04 | Lost acknowledgement after distributed commit may cause ambiguity | Application v0.3 residual risk unchanged; no production clearance |
| R04-05 | No authentication, durable state, distributed consensus or WAN outage testing | Explicitly out of scope for this staged harness |

No unresolved harness failure was observed in the completed final suite. No prior F01–F43 source-level issue is claimed resolved.
