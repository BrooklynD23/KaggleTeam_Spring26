---
estimated_steps: 5
estimated_files: 6
skills_used:
  - coding-standards
  - test
  - verification-loop
---

# T02: Implement CLI intake runtime and register a separate dispatcher branch

## Description
Wire the new photo intake runtime as a separate branch so teams can run canonical intake without changing existing shared ingestion behavior.

## Steps
1. Create `src/multimodal/photo_intake.py` CLI that loads `configs/multimodal.yaml`, reads the photo archive path, executes contract logic, and writes canonical artifacts under `outputs/multimodal/photo_intake/`.
2. Add `configs/multimodal.yaml` (extending `configs/base.yaml`) with dedicated photo archive and output-path settings.
3. Register a new dispatcher approach (photo intake) with its own stage definition and required outputs in `scripts/pipeline_dispatcher.py`.
4. Update launcher aliases/menus in `scripts/run_pipeline.py` so the approach is discoverable and runnable via canonical CLI.
5. Extend launcher/dispatcher tests for approach registration, command construction, and guard behavior.

## Must-Haves
- [ ] Shared pipeline stages remain unchanged and continue to target only existing JSON entities.
- [ ] New approach emits deterministic artifact paths and exits fail-closed on missing required artifacts.
- [ ] Launcher/dispatcher tests cover the new branch selection and stage wiring.

## Verification
- `python -m pytest tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py tests/test_photo_intake_contract.py -q`

## Inputs

- `src/multimodal/photo_intake_contract.py`
- `scripts/pipeline_dispatcher.py`
- `scripts/run_pipeline.py`
- `configs/base.yaml`

## Expected Output

- `src/multimodal/photo_intake.py`
- `scripts/pipeline_dispatcher.py`
- `scripts/run_pipeline.py`
- `configs/multimodal.yaml`

## Verification

python -m pytest tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py tests/test_photo_intake_contract.py -q

## Observability Impact

Signals added/changed: photo intake manifest/validation status fields and per-reason integrity counters. How a future agent inspects this: run `python scripts/pipeline_dispatcher.py --approach photo_intake --yes` and inspect `outputs/multimodal/photo_intake/{manifest.json,validation_report.json}`. Failure state exposed: explicit reason-coded failed phases and missing-output hard failure in dispatcher stage checks.
