---
estimated_steps: 4
estimated_files: 3
skills_used:
  - coding-standards
  - test
  - verification-loop
---

# T03: Add intake runtime contract tests and deterministic smoke verification

## Description
Close the slice with executable contract proof: runtime tests plus a lightweight verification command that asserts deterministic artifact shape and integrity diagnostics.

## Steps
1. Add `tests/test_photo_intake_runtime.py` that runs the intake CLI against small fixture inputs and asserts canonical artifacts/fields.
2. Add `scripts/verify_photo_intake_contract.py` to perform machine-readable assertions on manifest/validation outputs (including linked/missing/unreadable/usable counters and status vocabulary).
3. Document canonical command and verification flow in `README.md` for future slices.
4. Ensure verification command fails loudly with actionable diagnostics when artifacts are missing or malformed.

## Must-Haves
- [ ] Runtime test confirms deterministic artifact production and expected status semantics.
- [ ] Verification script checks integrity counters and required manifest fields, not just file existence.
- [ ] README includes canonical run + verify commands for photo intake.

## Verification
- `python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q`
- `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake`

## Inputs

- `src/multimodal/photo_intake.py`
- `src/multimodal/photo_intake_contract.py`
- `configs/multimodal.yaml`
- `README.md`

## Expected Output

- `tests/test_photo_intake_runtime.py`
- `scripts/verify_photo_intake_contract.py`
- `README.md`

## Verification

python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q && python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake

## Observability Impact

Signals added/changed: verification output reports exact missing/invalid contract fields and integrity counter mismatches. How a future agent inspects this: run `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake` after intake. Failure state exposed: contract drift and runtime artifact corruption are surfaced as deterministic assertion failures tied to specific fields.
