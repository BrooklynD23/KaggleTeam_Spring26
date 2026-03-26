# S01: Photo Intake Runtime Integration — UAT

**Milestone:** M005-i0a235
**Written:** 2026-03-26T07:52:09.829Z

# S01 UAT — Photo Intake Runtime and Contract Verification

## Preconditions

1. Run from repo root: `/mnt/c/Users/Danny/Documents/GitHub/KaggleTeam_Spring26`.
2. Python environment has project dependencies available.
3. `configs/multimodal.yaml` points at valid photo metadata/archive inputs.
4. Existing or generated artifact root: `outputs/multimodal/photo_intake/`.

---

## Test Case 1 — Contract + runtime + orchestration regressions stay green

**Goal:** Ensure the assembled code path (contract helpers, runtime loader, dispatcher wiring, launcher wiring) is regression-safe.

### Steps
1. Run:
   ```bash
   python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q
   ```

### Expected outcome
- Exit code `0`.
- Test report shows all tests passed (current expected count: 30).
- No missing-file failures for `tests/test_photo_intake_runtime.py`.

---

## Test Case 2 — Dispatcher branch executes and emits canonical artifacts

**Goal:** Validate the standalone `photo_intake` approach runs through `pipeline_dispatcher.py` and regenerates required outputs.

### Steps
1. Force a rerun of the stage:
   ```bash
   python scripts/pipeline_dispatcher.py --approach photo_intake --from-stage photo_intake_runtime --yes
   ```
2. Verify required files exist:
   ```bash
   test -f outputs/multimodal/photo_intake/manifest.json \
     && test -f outputs/multimodal/photo_intake/validation_report.json \
     && test -f outputs/multimodal/photo_intake/photo_metadata.parquet \
     && test -f outputs/multimodal/photo_intake/image_path_manifest.parquet
   ```

### Expected outcome
- Dispatcher stage `photo_intake_runtime` completes with exit code `0`.
- All four required artifacts are present after run.
- Runtime logs include row-count summary (`total`, `usable`, `missing`, `unreadable`).

---

## Test Case 3 — Contract verifier passes on generated artifacts

**Goal:** Confirm persisted artifact surfaces are self-consistent and contract-valid.

### Steps
1. Run:
   ```bash
   python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake
   ```

### Expected outcome
- Exit code `0`.
- Output includes: `Photo-intake contract verification passed ...`.
- Verifier confirms schema order, status/reason vocabulary, and row/counter parity between parquet and JSON reports.

---

## Test Case 4 — Operational diagnostics reflect healthy runtime state

**Goal:** Validate health/failure signaling surfaces that downstream slices will consume.

### Steps
1. Open `outputs/multimodal/photo_intake/manifest.json`.
2. Open `outputs/multimodal/photo_intake/validation_report.json`.
3. Confirm these fields:
   - `manifest.phases.metadata_load.status == "ok"`
   - `manifest.phases.path_resolution.status == "ok"`
   - `validation_report.status == "pass"`
   - `validation_report.errors == []`

### Expected outcome
- Both phase statuses are healthy (`ok`).
- Validation report is `pass` with no errors.
- `row_counts` and `integrity_counters` are present and non-negative.

---

## Edge Case A — Already-complete run path should skip safely

**Goal:** Ensure operators understand/observe idempotent skip behavior.

### Steps
1. Run:
   ```bash
   python scripts/pipeline_dispatcher.py --approach photo_intake --yes
   ```

### Expected outcome
- Exit code `0`.
- Console states the approach is already complete and defaults to skip.
- No failure or state corruption.

---

## Edge Case B — Verifier fails closed on drifted artifact payload

**Goal:** Ensure integrity checks catch schema/count/status drift.

### Steps
1. Copy artifacts to a temp directory.
2. Corrupt one payload field (example: edit copied `validation_report.json` status to `fail` or alter `row_counts`).
3. Run verifier against the copied root:
   ```bash
   python scripts/verify_photo_intake_contract.py --root <temp_corrupted_root>
   ```

### Expected outcome
- Exit code non-zero.
- Error message identifies the violated contract condition.
- Original canonical artifacts in `outputs/multimodal/photo_intake/` remain unchanged.
