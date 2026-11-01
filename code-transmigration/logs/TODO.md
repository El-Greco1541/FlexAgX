# Code transmigration TODO

- [x] Create isolated staged folder, preserve original shader hash.
- [x] Define the eight FX pass-to-module owners and publish typed module metadata.
- [x] Build serial correctness-first glue using validated CPU baseline ports.
- [x] Add no-null API rejection, replay, restart, rollback, and source-integrity tests.
- [ ] Decompose grouped CPU renderer into individually validated pass functions with deterministic intermediate image fixtures, comparing against legacy baseline before changing output.
- [ ] Define backend-neutral canonical intermediate colorspaces, precision and image storage contracts per pass; explicitly assess Oklab achromatic and transfer-function boundary cases.
- [ ] Add independent distributed server transports for ports, preserving atomic controller commit and bounded failures.
- [ ] Add authenticated ingress, filesystem quotas, native limits, platform CI and real ReShade compiler/GPU checks.
- [ ] Expand conformance fixtures from upstream shader and known F01–F43 findings; never present CPU results as GPU parity.
- [ ] Seek explicit operator authorization before production promotion or merge into main.
