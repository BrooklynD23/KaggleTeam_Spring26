# S04: Report and deck generated from shared narrative/evidence source — UAT

**Milestone:** M004-fjc2zy
**Written:** 2026-03-25T05:06:50.362Z

# S04: Report and deck generated from shared narrative/evidence source — UAT

**Milestone:** M004-fjc2zy  
**Written:** 2026-03-24

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: S04 deliverables are deterministic build artifacts and parity diagnostics generated from canonical JSON contracts; correctness is proved by reproducible commands and output comparison rather than subjective UI interaction.

## Preconditions

1. Canonical story artifacts exist:
   - `outputs/showcase/story/sections.json`
   - `outputs/showcase/story/tracks.json`
2. Python environment can run pytest and project scripts.
3. Output directory exists or is writable: `outputs/showcase/deliverables/`.

## Smoke Test

Run:

```bash
python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables
python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables
python scripts/check_showcase_parity.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --report outputs/showcase/deliverables/showcase_report.md --deck outputs/showcase/deliverables/showcase_deck.md --output outputs/showcase/deliverables/parity_report.json
```

Expected: all commands exit 0; `showcase_report.md`, `showcase_deck.md`, and `parity_report.json` are generated; parity summary reports `parity_passed=true`.

## Test Cases

### 1. Canonical executive narrative ordering is preserved in both deliverables

1. Generate report and deck using canonical story/tracks commands.
2. Open `outputs/showcase/deliverables/showcase_report.md` and `outputs/showcase/deliverables/showcase_deck.md`.
3. Verify executive sections appear in exact order: `prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`.
4. **Expected:** both artifacts preserve identical canonical ordering with no section reordering or omissions.

### 2. Claim-to-evidence pointer continuity (including blocked states)

1. Inspect evidence tables in report/deck artifacts.
2. Verify each claim row includes `surface_key`, `path`, `reason`, and `requirement_key` fields.
3. Confirm blocked M003 continuity surfaces are still represented as explicit rows (not dropped).
4. **Expected:** pointer fields are present for all evidence rows; blocked rows remain visible with canonical reason and requirement linkage.

### 3. Governance marker preservation across report and deck

1. Inspect report/deck governance sections/metadata rendering.
2. Verify markers include:
   - `internal_only=true`
   - `aggregate_safe=true`
   - `raw_review_text_allowed=false`
3. Run parity checker and inspect governance check in `parity_report.json`.
4. **Expected:** governance markers match canonical expected values in both artifacts and parity check passes `governance_markers`.

### 4. Parity diagnostics gate catches drift classes

1. Run `python -m pytest tests/test_showcase_parity_contract.py -q`.
2. Review fixture-backed failing scenarios for each drift class (section order, evidence keys, pointer fields, requirement keys, governance markers).
3. Run real parity command against generated deliverables.
4. **Expected:** regression suite passes (including fail-case assertions), real run returns exit 0 with `failed_checks=0`; checker is fail-closed when mismatches are introduced.

## Edge Cases

### Missing upstream continuity evidence should remain explicit, not silently removed

1. Use canonical story/tracks inputs that include blocked M003 continuity rows.
2. Build report/deck and run parity checker.
3. **Expected:** deliverables include blocked evidence diagnostics with canonical pointer fields; parity still passes because blocked-state representation matches source contract.

### Requirement drift hidden by set membership must still fail

1. Run parity contract tests that mutate row-level `requirement_key` mapping while preserving global requirement-ID set.
2. **Expected:** parity logic reports row-level requirement mismatch (not false pass), confirming per-evidence continuity enforcement.

## Failure Signals

- `scripts/check_showcase_parity.py` exits non-zero.
- `parity_report.json` contains `parity_passed=false` or non-empty `failing_check_ids`.
- Report/deck missing canonical sections or pointer columns.
- Governance marker values differ between expected/source and generated deliverables.

## Requirements Proved By This UAT

- R012 — Report/deck now derive from canonical story/evidence contract with enforced section/claim/evidence continuity.
- R013 (continuity support) — Governance markers are preserved and parity-validated across generated artifacts.
- R009 / R010 / R022 (continuity support) — Requirement-linked evidence pointers and blocked diagnostics are carried into report/deck and parity-checked.

## Not Proven By This UAT

- Full integrated local demo hardening across live Next.js runtime + report/deck + governance gate (S05 scope).
- No-live-query runtime behavior under full end-to-end demo execution (S05 integrated verification).

## Notes for Tester

- Treat `outputs/showcase/story/{sections.json,tracks.json}` as contract truth; report/deck are downstream renderings.
- If parity fails, inspect `parity_report.json` first; it is the authoritative drift triage surface and lists exact failing check classes and mismatch payloads.
- Optional Marp export of `showcase_deck.md` is packaging-only and should never replace parity validation as the acceptance gate.
