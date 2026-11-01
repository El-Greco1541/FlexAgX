# Research notes
- Correctness over speed: a new P0 clear pass is intentional overhead. Existing P2 clear is not removed.
- Fail closed on out-of-domain API input and do not echo user payloads.
- Modularity is through injected pure ports; actual GPU pipeline remains independent.
- No prior shader defects outside F38/F41 are claimed corrected.
- All values in archived JSON evidence avoid null and nonfinite outputs.
