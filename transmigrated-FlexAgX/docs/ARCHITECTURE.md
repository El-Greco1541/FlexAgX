# Correction-first architecture and API boundaries

```text
upstream immutable ReShade 1.2 shader  ---- SHA-256 pin
          |                                     |
          v                                     v
source correction (P0, guarded hue)    audit and parity tests
          |                                     |
          v                                     v
   transpiled FX candidate              correction_api/ports
          |                                     |
        ReShade GPU pending        FastAPI localhost probes
                                        |
                                   deterministic glue
```

- `reference/` is immutable. `shader/` is a deliberate source edit, not a production shader release.
- `correction_api/models.py`: strict bounded contracts, typed sentinels and validation.
- `correction_api/modules.py`: pure independent reset/hue operations.
- `correction_api/glue.py`: explicit injectible ports and serial coordination.
- `correction_api/api.py`: localhost correctness probe API. Not a pixel rendering API and not a ReShade wrapper.
- `tests/`: source structural checks, API validation, deterministic property/fuzz tests.
- `docs/`: correction ledger and decisions that must precede expansion.

The 67-counter preclear models the same histogram preparation policy as shader P0; it cannot establish GPU barrier guarantees. No mutable sessions or external services are included in this initial diagnostic API. Further API rendering should reuse the established v0.5.0 transaction protocol rather than reinvent it.

## v0.3.0 GPU temporal marker

The candidate shader adds `FA_TemporalBoot` (1x1 RGBA32F) as an explicit lifecycle discriminator. The single workgroup in the state pass validates its sentinel and previous frame index, then either reuses bounded prior controller state or constructs finite cold defaults. This source code is not proof of GPU scheduling/resource lifetime; consult `TEMPORAL_BOOT_V03.md`.
