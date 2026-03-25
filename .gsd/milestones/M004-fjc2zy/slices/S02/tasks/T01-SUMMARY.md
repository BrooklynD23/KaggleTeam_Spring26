---
id: T01
parent: S02
milestone: M004-fjc2zy
key_files:
  - configs/showcase.yaml
  - src/showcase/story_contract.py
  - src/showcase/__init__.py
  - scripts/build_showcase_story.py
  - tests/test_showcase_story_contract.py
  - outputs/showcase/story/sections.json
  - outputs/showcase/story/validation_report.json
key_decisions:
  - Enforced exact canonical executive section ordering in the story contract builder to prevent narrative drift.
  - Used intake-manifest surface status/reason as the single source of truth for story evidence readiness and blocked diagnostics.
  - Kept governance markers (`internal_only`, `aggregate_safe`, `raw_review_text_allowed`) in story artifacts for downstream UI/report parity.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T04:04:42.293Z
blocker_discovered: false
---

# T01: Add canonical showcase story contract generation with deterministic section/evidence diagnostics.

**Add canonical showcase story contract generation with deterministic section/evidence diagnostics.**

## What Happened

Implemented the S02/T01 story-contract surface end-to-end. I extended `configs/showcase.yaml` with a canonical executive mapping and fixed order (`prediction`, `surfacing`, `onboarding`, `monitoring`, `accountability`), then added `src/showcase/story_contract.py` to merge config + intake manifest into machine-readable section/evidence readiness artifacts. The builder emits deterministic governance markers, section status rollups, per-evidence blocked diagnostics, and explicit required/optional reason propagation keyed by `surface_key`, `path`, `reason`, and `requirement_key`. I added `scripts/build_showcase_story.py` to generate `outputs/showcase/story/sections.json` and `validation_report.json`, and exported the new contract API/constants via `src/showcase/__init__.py`. Regression coverage was added in `tests/test_showcase_story_contract.py` for ready and blocked branches (including missing/unmapped evidence semantics) and for CLI output-shape/file emission checks. I also recorded a project decision to enforce exact canonical section ordering at contract build time to prevent narrative drift across downstream UI/smoke consumers.

## Verification

Task verification passed with the contract test suite and story artifact generation command. Slice-level checks for this task scope were also run: Python + frontend test/build checks passed; the smoke-check command failed because `scripts/showcase_smoke_check.py` does not yet accept `--story` (planned for T03 in this slice).

## Verification Evidence
| Command | Exit | Verdict | Duration |
|---|---:|---|---:|
| `.venv-local/bin/python -m pytest tests/test_showcase_story_contract.py -q` | 0 | ✅ pass | 271ms |
| `.venv-local/bin/python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json` | 0 | ✅ pass | 55ms |
| `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1946ms |
| `npm --prefix showcase run build` | 0 | ✅ pass | 15737ms |
| `.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 45ms |

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `.venv-local/bin/python -m pytest tests/test_showcase_story_contract.py -q` | 0 | ✅ pass | 271ms |
| 2 | `.venv-local/bin/python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story && test -f outputs/showcase/story/sections.json && test -f outputs/showcase/story/validation_report.json` | 0 | ✅ pass | 55ms |
| 3 | `npm --prefix showcase run test -- --run` | 0 | ✅ pass | 1946ms |
| 4 | `npm --prefix showcase run build` | 0 | ✅ pass | 15737ms |
| 5 | `.venv-local/bin/python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --base-url http://127.0.0.1:3000` | 2 | ❌ fail | 45ms |


## Deviations

Used `.venv-local/bin/python` for verification commands because the default system Python in this environment did not have pytest available.

## Known Issues

`scripts/showcase_smoke_check.py` currently rejects the `--story` argument required by the slice-level verification command; this is expected to be addressed in T03.

## Files Created/Modified

- `configs/showcase.yaml`
- `src/showcase/story_contract.py`
- `src/showcase/__init__.py`
- `scripts/build_showcase_story.py`
- `tests/test_showcase_story_contract.py`
- `outputs/showcase/story/sections.json`
- `outputs/showcase/story/validation_report.json`
