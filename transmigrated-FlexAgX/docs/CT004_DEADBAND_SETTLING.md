# CT-004 — deadband/velocity settling, contract and evidence

**Candidate v0.4.0; research-only; production gate locked.**

## Source-linked defect and conservative proposed contract

Finding **F23**: the v0.3 S5 integrator assigned `target=x` for errors smaller than `Deadband`, but retained the preexisting `v`. The subsequent damping step moved `x` even when the target was neutral. This contradicts the UI statement that deadband ignores tiny brightness wobbles.

Finding **F24**: when `target==x`, the old ternary selected `DarkenSpeed`; it affected the decay and therefore the magnitude of artificial motion. In the new **staged** candidate, the branch becomes inert in the settled case.

CT-004 chooses **settle to rest** within inclusive deadband (`abs(e50-x) <= Deadband`): `v=0` and `x` unchanged; outside the band the original second-order update equations, direction choice, rate clamp and timestep limits are byte-for-byte retained. The inclusive boundary also settles an exactly neutral target when the Deadband slider is set to zero.

This resolves the *source-level drift behavior* under that proposed contract. **It remains a user-visible semantic choice under Operator review**, not a production policy. A decay-to-rest alternative would be visibly different and must be evaluated as a separate candidate.

## Executed verification

- v0.4.0 pytest 79/79 PASS (including 25 positional/velocity combinations, 2,000 random outside-band equality checks, source-mutation rejection and F29/F36 holdout checks).
- Two complete nine-phase, bounded, process-isolated CPU/static harness campaigns: 27,271 checks at 1,000 synthetic frames; 28,299 at 2,000; zero failures.
- Original shader SHA-256 verified identical to El-Greco1541 1.2.
- FX pass count is still nine: original eight plus histogram preclear. CT-004 changes only the S5 deadband fragment; the original .fx is preserved.

## Out of scope / not accepted

- No ReShade FX compiler/GPU execution or visual fidelity acceptance. The CPU oracle is an independent model of the modified math, *not* GPU evidence.
- **F29** current scene-cut internal-key correction has a dt-independent bounded jump after 0.10s persistence; applied exposure EV remains separately rate limited. Only diagnostic timer tests were added; no shader change.
- **F36** `AutoExposureStrength=0` removes auto-exposure contribution but does not disable state/key/knee adaptation. The previous choice is unchanged; no behavior approval assumed.
- F39/F40 gamut and transfer-encoding contracts remain untouched; F18/F32 hardware startup certification is still open.

## Reproduction

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
python -m harness.selftest
python -m harness.runner --seed 20261101 --frames 1000
python -m harness.runner --seed 731234 --frames 2000
```
