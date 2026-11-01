# Effect harness design — v0.2.0

## Objective

Evaluate the corrected FX candidate through reproducible static-source and CPU oracle tests. Fail closed and explicitly distinguish CPU approximations from native GPU execution.

## Assured surfaces

- **Source structural:** pinned SHA-256; exact nine-pass sequence; preclear coverage; origin guards; bounded loops and source-pass signatures.
- **Numerical oracles:** independently written HSV-free polar hue, 64-bin log luminance and 32-bit integer phase emulation, LUT boundary interpolation, and input population invariants.
- **Adversarial:** malformed/nonfinite requests, strict type/length/bounds rejection, meta-properties, load and concurrency.
- **Torture:** 1,000 and 2,000 sequences of synthetic RGB images whose phases, histogram totals and zero-on-call preclear behavior are checked with a CPU model. Not a GPU rendering benchmark.
- **Real loopback HTTP:** ASGI application launched as a subprocess, concurrent requests across eight client threads, process group killed and reaped on completion.
- **Harness self-fault:** deliberately corrupted evidence, missing files, count/seed mismatch, timeout and output flood.

## Commands

From `transmigrated-FlexAgX/`:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
python -m harness.selftest
python -m harness.toolchain_probe
python -m harness.runner --seed 20261101 --frames 1000
python -m harness.runner --seed 731234 --frames 2000
```

Runs create new `harness/results/fx-*` directories with JSON evidence; the runner verifies case count, a SHA-256 digest of the full case list, phase, seed, frame budget, status and child exit code. The process driver enforces a per-suite deadline, a 512 KiB output budget and 8 KiB retained output. It kills POSIX process groups to clean descendants. Evidence directory names are unique and do not overwrite prior evidence.

## Test evidence handling

- Two compact verified summaries in `harness/evidence/` are committed for review.
- Full case-level per-phase evidence is in the distribution ZIP, not the Git branch. `harness/results/` is ignored to avoid large/unreviewed datasets.
- The signed upstream MIT notice and shader reference remain unchanged.

## Threat model limits

Tests constrain this Python research harness and probes, not arbitrary native shader runtime operations. They do not establish ReShade compiler compatibility, GPU storage synchronization, full color science parity, durability, or secure external API service. In particular `FA_State` and `FA_HistPrev` first-use are known gaps.

If a native ReShade compiler and GPU test rig become available, create a separately authorized backend-specific adapter with cold-start, reload, disabled/bypass, odd framebuffer sizes, gamut extremes and replayable screenshot/telemetry fixtures. Store measured error thresholds, not marketing-equivalence claims.
