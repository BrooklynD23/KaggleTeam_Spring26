---
estimated_steps: 4
estimated_files: 4
skills_used:
  - coding-standards
  - test
  - verification-loop
---

# T01: Build the photo-intake contract module and integrity validator

## Description
Create a deterministic, testable contract layer for photo intake before wiring runtime orchestration.

## Steps
1. Add `src/multimodal/photo_intake_contract.py` with dataclasses/helpers that normalize photo metadata rows (`photo_id`, `business_id`, `caption`, `label`), compute resolved image paths, and aggregate integrity counters.
2. Define status vocabulary and validation helpers for contract outputs so missing metadata keys, missing files, and unreadable files are encoded as machine-readable reason codes.
3. Export contract entrypoints in `src/multimodal/__init__.py`.
4. Add `tests/test_photo_intake_contract.py` with deterministic fixtures covering linked/missing/unreadable/usable branches plus schema drift failures.

## Must-Haves
- [ ] Contract module emits deterministic integrity counters and stable key names for downstream slices.
- [ ] Validation helpers fail on schema/status vocabulary drift.
- [ ] Tests cover both healthy and degraded intake cases.

## Verification
- `python -m pytest tests/test_photo_intake_contract.py -q`

## Inputs

- `configs/base.yaml`
- `src/common/config.py`
- `src/ingest/load_yelp_json.py`
- `README.md`

## Expected Output

- `src/multimodal/photo_intake_contract.py`
- `src/multimodal/__init__.py`
- `tests/test_photo_intake_contract.py`

## Verification

python -m pytest tests/test_photo_intake_contract.py -q
