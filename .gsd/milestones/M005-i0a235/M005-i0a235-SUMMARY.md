---
id: M005-i0a235
title: "Future multimodal extensions — Context"
status: complete
completed_at: 2026-03-26T07:58:01.534Z
key_decisions:
  - D038 — Keep photo intake as its own single-stage dispatcher approach with fail-closed required outputs.
  - D039 — Lock deterministic photo-intake status/reason vocabulary and enforce strict schema/key validation.
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
lessons_learned:
  - For branch-local verification, compare against the integration baseline (`origin/main`) when local `main` has auto-mode commits; otherwise diff checks can produce false 'no code change' failures.
  - Contract-first multimodal intake is most reliable when runtime completion is paired with persisted-artifact verification (schema/vocabulary/count parity), not inferred from process exit codes alone.
  - Supporting both idempotent skip and explicit rerun flows in dispatcher UX reduces operational ambiguity during milestone closeout and incident recovery.
---

# M005-i0a235: Future multimodal extensions — Context

**M005 established a runnable, contract-verified standalone photo-intake multimodal foundation with dispatcher/launcher integration and fail-closed artifact verification.**

## What Happened

This milestone converted multimodal planning intent into a production-style intake surface that downstream multimodal experiments can trust. S01 implemented deterministic contract helpers and a runtime entrypoint, integrated the `photo_intake` approach into both dispatcher and launcher orchestration, and added a standalone verifier that checks persisted artifacts (manifest/validation/parquet) for schema, vocabulary, and count parity. During milestone closeout, the assembled regression suite passed, skip and forced-rerun dispatcher paths were validated, required artifact files were confirmed on disk, and manifest/report health signals were verified as healthy (`ok`/`pass`). The milestone therefore delivers the intended context bridge: reliable intake + machine-verifiable diagnostics, without over-committing to downstream feature/embedding scope.

## Success Criteria Results

- ✅ **Photo-intake runtime integration is complete and regression-safe.** Evidence: `python -m pytest tests/test_photo_intake_contract.py tests/test_photo_intake_runtime.py tests/test_pipeline_dispatcher_tracks_cd.py tests/test_run_pipeline_launcher.py -q` → `30 passed`.
- ✅ **Standalone dispatcher path executes and emits canonical artifacts.** Evidence: `python scripts/pipeline_dispatcher.py --approach photo_intake --from-stage photo_intake_runtime --yes` completed; artifacts verified present: `outputs/multimodal/photo_intake/manifest.json`, `validation_report.json`, `photo_metadata.parquet`, `image_path_manifest.parquet`.
- ✅ **Contract verifier validates persisted outputs.** Evidence: `python scripts/verify_photo_intake_contract.py --root outputs/multimodal/photo_intake` → pass message.
- ✅ **Operational diagnostics show healthy runtime state.** Evidence: manifest phase statuses `metadata_load=ok`, `path_resolution=ok`; validation report `status=pass`, `errors=[]`.
- ✅ **Idempotent operator path preserved.** Evidence: `python scripts/pipeline_dispatcher.py --approach photo_intake --yes` reports already complete and exits cleanly with skip behavior.

## Definition of Done Results

- ✅ **All milestone slices complete:** `S01` marked complete and summary/UAT artifacts exist.
- ✅ **Slice summaries present:** `.gsd/milestones/M005-i0a235/slices/S01/S01-SUMMARY.md` exists.
- ✅ **Cross-slice integration closure:** Milestone contains a single slice; integration points are internal and verified via dispatcher+launcher+contract verifier regression/tests.
- ✅ **Code-change verification passed:** Using integration baseline (`origin/main`) because local `main` is advanced in this worktree, `git diff --stat $(git merge-base HEAD origin/main) HEAD -- ':!.gsd/'` shows non-`.gsd` source/test/config changes including `src/multimodal/*`, `scripts/pipeline_dispatcher.py`, `scripts/run_pipeline.py`, `scripts/verify_photo_intake_contract.py`, and related tests.

## Requirement Outcomes

- No requirement status transitions were executed in this milestone closeout.
- R020 and R021 remain **deferred** (still intentionally post-core-path differentiators).
- Milestone evidence supports future mapping of R020 prerequisites by delivering a stable intake contract/runtime surface, but this milestone did not claim or validate full multimodal value proof or expansion gating.

## Decision Re-evaluation

| Decision | Still valid? | Evidence from delivered work | Revisit next milestone? |
|---|---|---|---|
| D038 (independent `photo_intake` dispatcher approach) | Yes | Dispatcher skip/rerun behavior and required-output contract checks worked in closeout verification without coupling to shared-ingestion prerequisites. | No |
| D039 (locked status/reason vocabulary + strict schema/key validation) | Yes | Contract/runtime tests plus `scripts/verify_photo_intake_contract.py` passed; persisted artifacts remained schema/vocabulary/count consistent. | No |

## Horizontal Checklist

No milestone-level horizontal checklist items were defined in the roadmap beyond S01 UAT/verification coverage, which were completed and evidenced above.

## Deviations

No scope deviation beyond closure hardening already captured in S01 (adding missing runtime test and standalone contract verifier to complete verification surfaces).

## Follow-ups

Next milestone should consume `image_path_manifest.parquet` for a bounded first multimodal experiment and preserve the same fail-closed manifest/validation contract semantics.
