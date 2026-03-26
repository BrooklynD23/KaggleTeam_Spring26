---
id: T01
parent: S01
milestone: M005-i0a235
key_files:
  - src/multimodal/photo_intake_contract.py
  - src/multimodal/__init__.py
  - tests/test_photo_intake_contract.py
  - .gsd/KNOWLEDGE.md
  - .gsd/DECISIONS.md
key_decisions:
  - Standardized photo-intake row statuses to `linked|missing|unreadable|usable` with explicit reason codes for machine-readable diagnostics.
  - Enforced strict deterministic key-order schema validation for metadata columns, image-path manifest columns, and integrity counters to fail fast on contract drift.
  - Documented and used `uv run --with pytest` for verification in this worktree because base Python lacks pytest/pip.
duration: ""
verification_result: mixed
completed_at: 2026-03-25T05:53:38.838Z
blocker_discovered: false
---

# T01: Implemented deterministic photo-intake contract helpers with status/reason validation and comprehensive branch/drift tests.

**Implemented deterministic photo-intake contract helpers with status/reason validation and comprehensive branch/drift tests.**

## What Happened

Implemented `src/multimodal/photo_intake_contract.py` as the new deterministic contract layer for photo intake. The module now normalizes raw metadata rows (`photo_id`, `business_id`, `caption`, `label`), resolves image paths, builds deterministic per-row intake records, aggregates integrity counters, and validates schema/vocabulary drift with explicit fail-fast errors. Added stable status vocabulary (`linked`, `missing`, `unreadable`, `usable`) and reason codes (`archive_missing`, `metadata_missing_keys`, `image_file_missing`, `image_unreadable`) to satisfy machine-readable diagnostics expectations for downstream runtime slices. Exported contract entrypoints in `src/multimodal/__init__.py` so later runtime wiring can import from the package surface directly. Added `tests/test_photo_intake_contract.py` with deterministic fixtures and assertions for linked/missing/unreadable/usable branches, counter determinism, and schema/status/counter drift failures. Also recorded the contract semantics decision in `.gsd/DECISIONS.md` via `gsd_decision_save` and appended an execution gotcha to `.gsd/KNOWLEDGE.md` about using `uv run --with pytest` in this worktree environment.

## Verification

Ran the task-level verification command successfully using `uv run --with pytest` because the default `/usr/bin/python3` environment lacks both `pytest` and `pip` in this worktree. `tests/test_photo_intake_contract.py` passed (5/5). Also ran the slice-level verification commands to track intermediate status: the expanded pytest command fails because `tests/test_photo_intake_runtime.py` is not implemented yet (T03), dispatcher `photo_intake` approach is not registered yet (T02), verification script does not exist yet (T03), and expected runtime artifacts are not produced yet (T02/T03). These are expected partial failures at T01 and do not block this task’s contract-layer completion.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run --with pytest python -m pytest tests/test_photo_intake_contract.py -q` | 0 | ✅ pass | 333ms |
| 2 | `uv run --with pytest python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q` | 4 | ❌ fail | 253ms |
| 3 | `python scripts/pipeline_dispatcher.py --approach photo_intake --yes` | 2 | ❌ fail | 59ms |
| 4 | `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake` | 2 | ❌ fail | 17ms |
| 5 | `test -f outputs/multimodal/photo_intake/manifest.json && test -f outputs/multimodal/photo_intake/validation_report.json && test -f outputs/multimodal/photo_intake/photo_metadata.parquet && test -f outputs/multimodal/photo_intake/image_path_manifest.parquet` | 1 | ❌ fail | 0ms |


## Deviations

Used `uv run --with pytest python -m pytest ...` instead of `python -m pytest ...` due local runtime missing `pytest` and `pip`. No code-scope deviations from the T01 implementation contract.

## Known Issues

Slice-level verification commands that depend on T02/T03 artifacts and wiring currently fail (missing runtime test/script, unregistered `photo_intake` approach, and absent output artifacts).

## Files Created/Modified

- `src/multimodal/photo_intake_contract.py`
- `src/multimodal/__init__.py`
- `tests/test_photo_intake_contract.py`
- `.gsd/KNOWLEDGE.md`
- `.gsd/DECISIONS.md`
