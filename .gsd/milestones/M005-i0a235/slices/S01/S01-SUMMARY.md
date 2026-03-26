---
id: S01
parent: M005-i0a235
milestone: M005-i0a235
provides:
  - Canonical standalone multimodal intake runtime branch (`photo_intake`) integrated with dispatcher/launcher.
  - Deterministic photo-intake artifact contract with stable status/reason vocabularies and schema/key drift enforcement.
  - Runnable verifier/test surfaces that downstream slices can use to assert intake integrity before building additional multimodal stages.
requires:
  []
affects:
  []
key_files:
  - src/multimodal/photo_intake_contract.py
  - src/multimodal/photo_intake.py
  - src/multimodal/__init__.py
  - configs/multimodal.yaml
  - scripts/pipeline_dispatcher.py
  - scripts/run_pipeline.py
  - scripts/verify_photo_intake_contract.py
  - tests/test_photo_intake_contract.py
  - tests/test_photo_intake_runtime.py
  - tests/test_pipeline_dispatcher_tracks_cd.py
  - tests/test_run_pipeline_launcher.py
  - .gsd/PROJECT.md
  - .gsd/KNOWLEDGE.md
  - .gsd/DECISIONS.md
key_decisions:
  - D038 — Integrated photo intake as an independent single-stage dispatcher approach with required-output fail-closed checks.
  - D039 — Locked photo-intake status/reason vocabulary and strict deterministic schema/key validation for machine-readable diagnostics.
  - Added direct verifier command semantics (`scripts/verify_photo_intake_contract.py`) so artifact truth is validated from persisted contract surfaces, not assumed from runtime completion alone.
patterns_established:
  - Contract-first runtime pattern: every intake run emits paired machine-readable diagnostics (`manifest.json` + `validation_report.json`) plus deterministic parquet artifacts under a canonical output root.
  - Dispatcher extension pattern: register new approach as a single-stage branch with explicit required outputs, then expose the same approach in the interactive launcher alias/menu surface.
  - Verification closure pattern: pair pytest contract/runtime coverage with a standalone post-run verifier that re-computes schema/vocabulary/count agreement from persisted artifacts.
observability_surfaces:
  - outputs/multimodal/photo_intake/manifest.json
  - outputs/multimodal/photo_intake/validation_report.json
  - outputs/multimodal/photo_intake/photo_metadata.parquet
  - outputs/multimodal/photo_intake/image_path_manifest.parquet
  - scripts/verify_photo_intake_contract.py
  - python scripts/pipeline_dispatcher.py --approach photo_intake --from-stage photo_intake_runtime --yes
drill_down_paths:
  - .gsd/milestones/M005-i0a235/slices/S01/tasks/T01-SUMMARY.md
  - .gsd/milestones/M005-i0a235/slices/S01/tasks/T02-SUMMARY.md
duration: ""
verification_result: passed
completed_at: 2026-03-26T07:52:09.824Z
blocker_discovered: false
---

# S01: Photo Intake Runtime Integration

**Delivered a deterministic, standalone `photo_intake` pipeline branch with contract-validated artifacts, runtime regression coverage, and a fail-closed verification command for downstream multimodal work.**

## What Happened

S01 converted multimodal photo intake from planning intent into a runnable, contract-enforced pipeline surface. The slice now includes deterministic intake-contract helpers (`src/multimodal/photo_intake_contract.py`) with explicit row-status/reason vocabularies and strict schema/key validation, a runtime entrypoint (`src/multimodal/photo_intake.py`) configured via `configs/multimodal.yaml`, and first-class dispatcher/launcher integration through a dedicated `photo_intake` approach in `scripts/pipeline_dispatcher.py` and `scripts/run_pipeline.py`.

To close the slice verification gap left in T02, the slice added missing runtime test coverage (`tests/test_photo_intake_runtime.py`) and implemented a fail-closed diagnostics command (`scripts/verify_photo_intake_contract.py`) that cross-checks manifest/validation JSON payloads against parquet schema/vocabulary/count truth. This converted prior known-issue failures (`tests/test_photo_intake_runtime.py` missing and verifier script missing) into passing checks while preserving deterministic artifact semantics for downstream consumers.

Operationally, the slice establishes `outputs/multimodal/photo_intake/` as the canonical intake root with `manifest.json`, `validation_report.json`, `photo_metadata.parquet`, and `image_path_manifest.parquet`, and demonstrates both skip-on-complete behavior and forced rerun behavior via dispatcher controls.

## Verification

Executed and passed the slice-level assembled checks for the delivered runtime/contract branch:

1) `python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q` → 30 passed.
2) `python scripts/pipeline_dispatcher.py --approach photo_intake --yes` → pass (expected skip when already complete, exit 0).
3) `python scripts/pipeline_dispatcher.py --approach photo_intake --from-stage photo_intake_runtime --yes` → pass (forced rerun, stage completed, artifacts regenerated).
4) `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake` → pass.
5) `test -f outputs/multimodal/photo_intake/manifest.json && test -f outputs/multimodal/photo_intake/validation_report.json && test -f outputs/multimodal/photo_intake/photo_metadata.parquet && test -f outputs/multimodal/photo_intake/image_path_manifest.parquet` → pass.

Observability spot-check confirmed manifest/validation agreement and deterministic status/reason counter surfaces.

## Operational Readiness (Q8)

- **Health signal:** `outputs/multimodal/photo_intake/manifest.json` shows `phases.metadata_load.status=ok` and `phases.path_resolution.status=ok`, with `validation_report.json` status `pass`.
- **Failure signal:** `scripts/verify_photo_intake_contract.py` exits non-zero on schema/vocabulary/count drift, and runtime contract failures raise `PhotoIntakeContractError` with explicit reasons.
- **Recovery procedure:** rerun `python scripts/pipeline_dispatcher.py --approach photo_intake --from-stage photo_intake_runtime --yes`, then re-run `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake` to confirm restored artifact integrity.
- **Monitoring gaps:** no scheduled/continuous monitor yet for intake freshness, archive growth, or repeated reason-code trend alerts; current checks are operator-invoked.

## New Requirements Surfaced

None.

## Deviations

The slice needed one closure expansion beyond the T02 checkpoint: adding `tests/test_photo_intake_runtime.py` and `scripts/verify_photo_intake_contract.py` so the previously missing slice-level verification surfaces could pass. T02’s documented carry-forward reconstruction of absent T01 files remained intact.

## Known Limitations

This slice only establishes intake/runtime contract plumbing; it does not yet implement downstream multimodal feature extraction, embeddings, or model-training consumption. Current real-run artifacts reflect the available local photo metadata/image archive contents and therefore do not exercise large-scale throughput or richer label-taxonomy branches.

## Follow-ups

Use this intake bundle as the required upstream dependency for the next multimodal slice(s): add bounded feature/embedding construction stages that consume `image_path_manifest.parquet`, preserve no-raw-text/privacy boundaries, and keep fail-closed manifest/validation semantics aligned with this contract surface.

## Files Created/Modified

- `src/multimodal/photo_intake_contract.py` — Implemented deterministic intake-contract normalization, status/reason assignment, schema/vocabulary validation, and artifact writers.
- `src/multimodal/photo_intake.py` — Added runtime CLI to load metadata NDJSON, resolve configured paths, execute contract, and log row-count outcomes.
- `src/multimodal/__init__.py` — Exported multimodal photo-intake contract entrypoints for package-level imports.
- `configs/multimodal.yaml` — Added canonical multimodal photo-intake configuration block (metadata path, archive dir, output root).
- `scripts/pipeline_dispatcher.py` — Registered `photo_intake` approach and stage required outputs; preserved direct script import reliability via repo-root sys.path insertion.
- `scripts/run_pipeline.py` — Added launcher menu labels/aliases/ordering for photo intake approach.
- `scripts/verify_photo_intake_contract.py` — Added fail-closed artifact verifier to assert manifest/validation/parquet schema-vocabulary-count continuity.
- `tests/test_photo_intake_contract.py` — Added deterministic contract tests for linked/missing/unreadable/usable branches and schema/counter drift failures.
- `tests/test_photo_intake_runtime.py` — Added runtime tests for NDJSON loading errors, config guards, and successful artifact emission.
- `tests/test_pipeline_dispatcher_tracks_cd.py` — Extended dispatcher regression coverage to include photo intake approach registration, stage contract, and shared-prereq bypass.
- `tests/test_run_pipeline_launcher.py` — Extended launcher regression coverage for photo-intake aliases/command construction/menu inclusion.
- `.gsd/KNOWLEDGE.md` — Captured photo-intake rerun-vs-skip verification gotcha for future agents.
- `.gsd/PROJECT.md` — Updated current-state and milestone narrative to reflect M005 S01 intake-runtime completion.
- `.gsd/DECISIONS.md` — Recorded D039 for photo-intake status/reason contract semantics.
