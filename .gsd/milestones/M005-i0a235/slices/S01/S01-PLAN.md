# S01: Photo intake and integrity contract (separate branch)

**Goal:** Establish a separate, reproducible photo-intake branch that ingests Yelp photo metadata and image-file references into deterministic contract artifacts with explicit integrity diagnostics for linkability, missing files, unreadable files, and usable coverage.
**Demo:** After this slice, the team can run a canonical photo-intake command and inspect deterministic artifacts that show how many photos were discovered, linked, missing, unreadable, and usable for downstream fusion.

## Must-Haves

- A standalone photo-intake command exists and does not mutate the existing shared JSON ingestion path.
- Intake outputs include deterministic contract artifacts: normalized photo metadata parquet, image-path manifest parquet, and machine-readable manifest/validation diagnostics.
- Integrity diagnostics report linkability and file-health counts (linked, missing, unreadable, usable) with stable status semantics.
- Dispatcher/launcher wiring allows repeatable execution through a canonical approach name.
- Regression tests fail if schema/status vocabulary or deterministic intake semantics drift.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q`
- `python scripts/pipeline_dispatcher.py --approach photo_intake --yes`
- `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake`
- `test -f outputs/multimodal/photo_intake/manifest.json && test -f outputs/multimodal/photo_intake/validation_report.json && test -f outputs/multimodal/photo_intake/photo_metadata.parquet && test -f outputs/multimodal/photo_intake/image_path_manifest.parquet`

## Observability / Diagnostics

- Runtime signals: intake phase status plus reason-coded counters (`archive_missing`, `metadata_missing_keys`, `image_file_missing`, `image_unreadable`) in manifest and validation report.
- Inspection surfaces: `outputs/multimodal/photo_intake/{manifest.json,validation_report.json,photo_metadata.parquet,image_path_manifest.parquet}` and `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake`.
- Failure visibility: per-phase status, integrity-count breakdown, and contract-field assertion failures with explicit missing/invalid keys.
- Redaction constraints: no raw review text and no raw image redistribution; outputs remain metadata/aggregate-safe.

## Integration Closure

- Upstream surfaces consumed: `configs/base.yaml`, `src/common/config.py`, `src/ingest/load_yelp_json.py`, `scripts/pipeline_dispatcher.py`, `scripts/run_pipeline.py`.
- New wiring introduced in this slice: `src/multimodal/photo_intake.py` runtime, `src/multimodal/photo_intake_contract.py` contract layer, and a dedicated dispatcher/launcher approach (`photo_intake`).
- What remains before the milestone is truly usable end-to-end: S02 fusion dataset construction, S03 multimodal baseline run + compute ledger, S04 expand-or-stop decision gate.

## Tasks

- [ ] **T01: Build the photo-intake contract module and integrity validator** `est:1h 45m`
  - Why: Downstream fusion and experiments need a deterministic intake contract before any runtime wiring; otherwise missing/unreadable image issues stay implicit.
  - Files: `src/multimodal/photo_intake_contract.py`, `src/multimodal/__init__.py`, `tests/test_photo_intake_contract.py`, `configs/base.yaml`
  - Do: Implement metadata normalization and image-path resolution helpers; define status vocabulary and validation helpers for integrity counters; add pytest coverage for linked/missing/unreadable/usable and schema-drift branches.
  - Verify: `python -m pytest tests/test_photo_intake_contract.py -q`
  - Done when: Contract tests pass and the module exposes deterministic, machine-validated intake payloads for all integrity branches.

- [ ] **T02: Implement CLI intake runtime and register a separate dispatcher branch** `est:2h`
  - Why: The slice demo requires a canonical command path that is explicitly separate from shared JSON ingestion.
  - Files: `src/multimodal/photo_intake.py`, `scripts/pipeline_dispatcher.py`, `scripts/run_pipeline.py`, `configs/multimodal.yaml`, `tests/test_pipeline_dispatcher_tracks_cd.py`, `tests/test_run_pipeline_launcher.py`
  - Do: Add a photo-intake CLI that reads multimodal config and emits canonical artifacts; add `photo_intake` approach wiring to dispatcher/launcher without changing shared stages; extend dispatcher/launcher tests for new approach behavior.
  - Verify: `python -m pytest tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py tests/test_photo_intake_contract.py -q`
  - Done when: `photo_intake` is discoverable and runnable via dispatcher/launcher, and approach wiring fails closed when required outputs are missing.

- [ ] **T03: Add intake runtime contract tests and deterministic smoke verification** `est:1h 30m`
  - Why: Slice closure needs executable proof that runtime outputs are valid and diagnosable, not just code-path existence.
  - Files: `tests/test_photo_intake_runtime.py`, `scripts/verify_photo_intake_contract.py`, `README.md`
  - Do: Add runtime pytest coverage that executes intake against fixtures and asserts artifact shape/status semantics; add verification script that checks required fields and counters; document canonical run + verify commands.
  - Verify: `python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q && python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake`
  - Done when: Runtime tests and verification script pass, and failures report precise contract/key drift.

## Files Likely Touched

- `configs/base.yaml`
- `configs/multimodal.yaml`
- `src/multimodal/__init__.py`
- `src/multimodal/photo_intake_contract.py`
- `src/multimodal/photo_intake.py`
- `scripts/pipeline_dispatcher.py`
- `scripts/run_pipeline.py`
- `scripts/verify_photo_intake_contract.py`
- `tests/test_photo_intake_contract.py`
- `tests/test_photo_intake_runtime.py`
- `tests/test_pipeline_dispatcher_tracks_cd.py`
- `tests/test_run_pipeline_launcher.py`
- `README.md`
