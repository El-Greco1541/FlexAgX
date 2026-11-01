# CT-003 — F18/F32 temporal cold-start correction v0.3.0

**Scope:** staged, CPU/static acceptance only. **Candidate SHA-256:** `9116e0c2f4d13214b678f387bf05723348d0910117755e9a4c3de6addb894c68`.

## Threat and failure mode

The original state pass loads `FA_State` and `FA_HistPrev` without proving their previous contents. On first use or after a technique has been disabled, uninitialized or stale values may contaminate the exposure key, scene cut detection, knee and warmup. The F41 histogram preclear does not initialize these resources.

## Source change

- Add single-pixel `RGBA32F FA_TemporalBoot` with distinct exact marker constants and two exact 16-bit limbs of the **previously processed game framecount**, protecting precision across 32-bit counter values.
- Only accept a retained state when the boot marker matches the immediately preceding frame and saved state fields are finite and bounded.
- On every invalid/cold marker, derive safe exposure state defaults and use the current histogram as the previous-scene baseline. This prevents a fabricated scene cut from arbitrary previous-scene storage.
- Use a barrier before dependent shared-memory reads, then store the marker after controller state and previous-scene writes in the same single-workgroup state pass.
- On bypass, do not refresh the marker; re-enabling triggers reinitialization due to framecount discontinuity.

## Acceptance evidence

- 48 pytest tests passed (new temporal oracle and source-mutation tests).
- Two completed 8-phase harness campaigns: **19,669/19,669** at 1,000 simulated frames, **20,697/20,697** at 2,000; **40,366 cumulative executions**, zero failures.
- New temporal phase: **8,111** deterministic checks per campaign covering marker mismatch, random frame discontinuities, poisoned components, normalization and uint32 framecount wraparound.
- Reference shader remains byte-identical to release 1.2; nine effect passes remain in order.

## Explicit limitations (not resolved by passing tests)

- No ReShade FX compile or GPU execution. `tex2Dfetch` and `tex2Dstore` on storage resources, barriers and resource-lifetime semantics require target GPU verification.
- Marker validation is a guard against ordinary uninitialized and stale contents, **not a mathematical guarantee against coincidental marker collisions**, arbitrary state corruption or backend nondeterminism.
- It does not guarantee reset on all effect reload patterns if resources are retained and framecounts are consecutive. A host lifecycle signal would be required for a strict reload contract.
- Real GPU framebuffer, temporal state, and scene-cut behavior have not been compared with CPU fixtures.
- No policy changes to F23/F24, F29/F36 or F39/F40.

## Native acceptance matrix to run before closure

| Scenario | Required observation |
| --- | --- |
| Fresh process / first active frame | Finite state; no random flash or bogus scene-cut timer |
| Effect enabled mid-session | Cold-start despite nonzero game framecount |
| Disabled for one or more game frames, then enabled | Reinitialize exposure and histogram comparison |
| Effect reload while enabled | Defined reset/reuse behavior; test texture recreation and GPU resource barriers |
| Color profiles, all-black and white images | Deterministic cold outputs and finite LUT |
| Odd-sized frames, backend change, resolution change | No stale histogram/state dependency |
| D3D11, D3D12, Vulkan, OpenGL 4.3 | FX compiles, warnings triaged, pass ordering and UAV barriers verified |
