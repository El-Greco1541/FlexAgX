# Cleanup audit and scope — v0.6.0 staging

**Synchronized:** 2026-11-01. **Type:** documentation and integrity-ledger housekeeping only.

## Issues corrected

1. README mixed the v0.2.0 harness headline and historic versions with current v0.6.0 claims; replaced it with a single current overview and concise stage history.
2. TODO carried resolved source-level tasks as unchecked and repeated release blockers; replaced it with distinct **completed-source** and **open-GPU/policy** sections.
3. ROADMAP numbered old release goals inconsistently with the actual completed v0.3–v0.6 milestones; synchronized the actual version map.
4. `.gitignore` repeated SQLite/database rules; consolidated them without weakening the coverage.
5. Added a persistent branch/PR synchronization snapshot and explicitly recorded the latest shader line as outside the older pull requests.
6. Rebuilt `MANIFEST.json` and `SHA256SUMS.txt` after doc edits; unchanged original/candidate shader and executable source files remain hash-identical to the v0.6.0 staging baseline.

## Preserved by design

The original FX reference, corrected FX candidate, Python API implementation, harness and tests, case summary reports, historical ledgers, prior branches, root readme/LICENSE, and existing draft PRs are left untouched. No source code changes, feature expansion, GPU run, production gate clearance or merge is implied.

## Validation procedure

- Verify all `MANIFEST.json` file hashes and run `sha256sum -c SHA256SUMS.txt` from the project root (if available).
- Run `python -m pytest -q tests` and `python -m harness.selftest`; these are tests of the existing CPU/static code, not of native GPU execution.
- Compare `reference/FlexAgX_1.2.fx`, `shader/FlexAgX_transmigrated.fx`, `correction_api`, `harness`, and `tests` against the pinned pre-sync manifest.
- Confirm the GitHub remote branch inventory and non-mutation of `main` after push.

## Completed local synchronization revalidation

- **113/113 pytest regression tests passed** in the documentation-only synchronization worktree.
- **16/16 isolated harness self-tests passed**, including evidence-corruption and subprocess timeout/output bounds.
- **79/79 tracked file hashes passed** and both FX source hashes are unchanged.
- The original 125,545-check v0.6.0 campaign is archived evidence; full campaigns were **not rerun** during this housekeeping pass.
- Native ReShade/GPU acceptance was not run.
