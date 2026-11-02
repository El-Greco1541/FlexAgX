# CT-007 — Native ReShade FX/GPU acceptance protocol

**Scope:** evidence collection, not an implementation, GPU execution, release approval, or shader correction. **Production gate: LOCKED.** Candidate shader is the unchanged v0.6.0 `.fx` file. Native tests must be performed on a machine with ReShade, a supported graphics API, and a controlled non-networked graphics host.

## 1. Why this phase is necessary

Existing harness totals cover shader *text*, numerical oracles, API boundary checks, and simulated frames. Generic HLSL/GLSL validators cannot validate ReShade FX's full effects, storage images, techniques, and uniform annotations. The ReShade project documents a standalone FX compiler built from its own `source/effect_*.*` implementation, as well as the ReShade runtime/add-on API. Do not substitute an unrelated `fxc.exe` or `dxc` run for compiling the `.fx` effect.

References: https://github.com/crosire/reshade/blob/main/README.md and https://github.com/crosire/reshade/blob/main/REFERENCE.md .

## 2. Generate a pinned, deterministic plan

From `transmigrated-FlexAgX/` on a disposable development machine:

```bash
python -m pip install -r requirements-dev.txt
python -m native_acceptance probe
python -m native_acceptance prepare --output ../native-run-local
```

The `prepare` operation refuses a nonempty target. Keep the generated folder **outside** `transmigrated-FlexAgX/` and outside the public git tree. The five source fixtures are 96x64 8-bit SDR PNG files: grayscale ramp, saturated patches, highlight steps, dark scene and bright scene. They are **not** HDR/superwhite inputs and cannot determine F30/F31.

The output has `plan.json`, `capture_record.template.json`, `fixtures/` and an empty `captures/` directory. No fake compilation transcript or GPU image is generated.

## 3. Capture actual ReShade evidence on the target machine

Use a controlled **offline** graphics host that displays fixtures without animation, temporal noise, postprocessing, color-management changes or rescaling. Render captures at a fixed resolution with one backend at a time. Document ReShade version, GPU model, driver, host application, OS and backend.

1. Install ReShade from its official project, point its shader search path at the candidate file (`shader/FlexAgX_transmigrated.fx`), and have ReShade compile/load it. Capture the **actual** effect/reload diagnostic log under `native-run-local/logs/ReShade.log`. A successful load must be checked in the ReShade interface; a manually edited log or a fake compiler verdict is prohibited.
2. For each selected backend (D3D11, D3D12, OpenGL >= 4.3, Vulkan) create a separate bundle. Do not infer compatibility with untested backends. Ensure host/game rules allow ReShade use. Prefer a private test host rather than a networked or anti-cheat application.
3. Capture `zero_baseline.png` (effect disabled) and `zero_effect.png` (effect enabled, `OverallStrength=0`, `DebugView=0`) **at identical settled input frames**, using the same capture path. The verifier demands exact RGB equality for these two PNG images. If the host cannot produce deterministic pairs, this test is blocked rather than relaxed.
4. Capture `neutral_gray.png` with gray ramp to inspect achromatic hue safety; `saturated_color.png` with saturated patches and a non-neutral white balance to inspect the post-blend gamut behavior. Save real screenshots as 8-bit PNG using identical crop dimensions. 8-bit PNG cannot prove GPU intermediate-range containment or HDR correctness.
5. Capture `first_frame.png` at initialization and `reload_frame.png` directly after a ReShade effect reload; inspect `FA_State`, `FA_HistPrev` reset behavior and exposure smoothness. Capture `cut_first.png` and `cut_second.png` at the first and second divergent scene observations, including frame timing and current histogram/scene-cut diagnostics in the operator's notes. Screenshots alone do **not** prove temporal control correctness.
6. Record the exact ReShade version, backend, driver and candidate SHA-256; compute SHA-256 for every PNG and the actual diagnostic log. Copy the template to `capture_record.json`, set `native_execution_reported=true`, `synthetic_or_mock=false`, and fill out all required fields. Never upload private logs/screenshots without review.

This is a **manual collection protocol**. There is no automated native shader process launcher in v0.7; it must not be described as an actual successful compile or GPU test until a real machine completes it.

## 4. Verify the evidence integrity and deterministic bypass

```bash
python -m native_acceptance verify --bundle ../native-run-local
```

The verifier checks original/candidate source hashes, fixed fixtures, file size/path containment, compile log digest, real-execution declaration, supported backend, capture integrity and identical RGB capture dimensions. It also tests exact bypass screenshot equality. It reports **`EVIDENCE_READY_FOR_INDEPENDENT_REVIEW`** when all declared evidence and the bypass comparison are internally consistent. This is **not** certification: a fabricated log and capture set with internally consistent hashes cannot be distinguished from real evidence by an offline checker. Independent operator/peer review must establish provenance, scene control and test design before any acceptance decision.

It returns `BLOCKED_OR_INVALID` on missing or conflicting artifacts. An empty generated template must **fail** verification. No run is declared passed because a compiler executable is merely present.

## 5. Required acceptance matrix (not automatic success)

| Area | Evidence required | Gate |
| --- | --- | --- |
| FX compiler / F19 | Actual ReShade compile diagnostic plus loaded technique, version and backend | Human reviewer confirms no fatal errors |
| Source identity | SHA-256 of unchanged upstream and candidate | Verifier rejects mismatch |
| F38 / F41 | Neutral gray, histogram reset, preclear ordering | GPU resources and barriers reviewed |
| F18 / F32 | First-ever frame, disable/re-enable, reload, retained state across warm/cold sessions | Reviewer inspects state and continuity |
| F23 / F24 | Deadband entry, settling, repeated slow frames | Reviewer checks temporal trace |
| F29 / F36 | One vs two discrepant observations, freeze, auto-strength zero | Reviewer checks scene-cut control trace |
| F39 | Saturated/highlight patches at WB extremes, linear postblend bounds | Reviewer obtains float-capable debug capture where available |
| F40 | 0% exact bypass and near-zero cross-encoding comparison | Operator selects desired conversion policy |
| F30 / F31 | Negative/superwhite/HDR encoded-domain fixtures | **Not covered by current SDR fixtures; separate policy and capture path required** |

**No global GPU PASS** can be inferred from one backend, manual description, 8-bit screenshot, or source/static harness success. Real compile and per-backend pass/fail must remain explicit. Cross-platform and multiple GPU-vendor testing are separate requirements.

## 6. Security and privacy

Keep host logs, captured images, full paths, hardware metadata, driver details and raw session data **out of public git**. `.gitignore` excludes `native-run*`, `native-evidence*`, `capture_record.json` and `captures/`. Only source code, synthetic fixture generator, tests and a redacted report are staged. Native evidence may contain private application content.

## Outcome for current run

The development container had Python 3.13 and Pillow; no ReShade FX executable, GPU detector or native graphics runtime was found. The plan generator, negative controls and evidence verifier were tested, but **no .fx compilation or GPU rendering was executed here**. Native verdict is `NOT_EXECUTED`, with acceptance still open.
