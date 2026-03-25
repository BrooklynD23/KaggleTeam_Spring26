# S04: Trust narrative and intern explainer workflow

**Goal:** Ground the showcase planning lane in an honest trust-marketplace story and a repeatable intern-explainer workflow that both point to the existing aggregate-safe export bundle instead of inventing new evidence surfaces.
**Demo:** The repo contains dedicated showcase planning docs for the trust narrative and intern explainer workflow, the existing showcase feature/sprint/phase docs link to them, and a dedicated pytest drift harness proves the content stays aligned with exported evidence, prior-art intern docs, and the internal aggregate-safe boundary.

## Must-Haves

- The showcase lane gets dedicated S04-owned docs for the trust-marketplace narrative and the intern explainer workflow under `.gsd/feature-plans/showcase-system/`.
- The trust narrative maps prediction, surfacing, monitoring, onboarding, and accountability to Tracks A-E using `outputs/exports/eda/` evidence, including Track D blocker truth and Track E metadata-only validity evidence.
- The intern explainer workflow states when to invoke the explainer-style agent, what inputs it must read first, what outputs it should produce, and what guardrails it must follow for intern-friendly, no-raw-text explanations.
- Existing showcase planning docs are back-linked to the new S04 docs so later M004 agents discover them from the canonical lane instead of re-researching the repo.
- A dedicated pytest contract test protects the new docs and cross-links so `R004` can be validated by execution rather than prose review.

## Proof Level

- This slice proves: contract
- Real runtime required: no
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_trust_narrative_workflow.py`
- `python - <<'PY'
from pathlib import Path
paths = [
    Path('.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md'),
    Path('.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md'),
    Path('.gsd/feature-plans/showcase-system/FEATURE_PLAN.md'),
    Path('.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md'),
    Path('.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md'),
]
for path in paths:
    assert path.exists(), path
print('showcase narrative surfaces present')
PY`
- `python - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path('outputs/exports/eda/manifest.json').read_text(encoding='utf-8'))
assert manifest['scope'] == 'internal'
assert manifest['safety_boundary'] == 'aggregate-safe'
assert manifest['status_totals']['existing'] == 6
assert manifest['status_totals']['missing'] == 109
track_d = next(track for track in manifest['tracks'] if track['approach'] == 'track_d')
assert 'outputs/tables/track_a_s5_candidate_splits.parquet' in track_d['blocked_by']
track_e = json.loads(Path('outputs/exports/eda/tracks/track_e/manifest.json').read_text(encoding='utf-8'))
validity = track_e['metadata_summaries'][0]
assert validity['export_mode'] == 'metadata_only'
assert validity['summary'] == 'No findings detected.'
print('showcase diagnostics remain inspectable and honest')
PY`

## Observability / Diagnostics

- Primary runtime-inspection surfaces are `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and the per-track manifests under `outputs/exports/eda/tracks/`.
- Failure visibility must stay machine-checkable: Track D blocker truth is read from `blocked_by`, root completeness from `status_totals`, and Track E validity evidence from `metadata_summaries` with `export_mode: metadata_only`.
- Documentation created in this slice must cite concrete repo paths so later agents can inspect source-of-truth files directly instead of relying on paraphrase.
- Redaction constraints remain active in every diagnostic surface: scope must stay `internal`, safety boundary must stay `aggregate-safe`, and no raw review text or copied `.parquet`/`.ndjson`/`.log` payloads may be introduced into showcase planning docs.

## Integration Closure

- Upstream surfaces consumed: `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `outputs/exports/eda/tracks/track_a/summary.md`, `outputs/exports/eda/tracks/track_b/summary.md`, `outputs/exports/eda/tracks/track_c/summary.md`, `outputs/exports/eda/tracks/track_d/summary.md`, `outputs/exports/eda/tracks/track_d/manifest.json`, `outputs/exports/eda/tracks/track_e/summary.md`, `outputs/exports/eda/tracks/track_e/manifest.json`, `CoWork Planning/yelp_project/docs_agent/AGENTS.md`, `CoWork Planning/yelp_project/docs/intern/README.md`
- New wiring introduced in this slice: `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md` and `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md` become the canonical S04 content contract, then `FEATURE_PLAN.md`, `SPRINT.md`, `PHASE-01-export-driven-experience-map.md`, and `tests/test_trust_narrative_workflow.py` are wired to those docs.
- What remains before the milestone is truly usable end-to-end: S05 still needs to verify the narrative layer together with the export bundle and planning architecture in one integrated handoff pass.

## Tasks

- [x] **T01: Author export-grounded trust narrative and explainer docs** `est:45m`
  - Why: S04 directly owns `R004`, and the milestone cannot tell the trust-marketplace story honestly until the showcase lane contains dedicated docs grounded in the current export bundle and prior-art intern guidance.
  - Files: `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`, `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`, `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, `outputs/exports/eda/tracks/track_d/manifest.json`, `outputs/exports/eda/tracks/track_e/manifest.json`, `CoWork Planning/yelp_project/docs_agent/AGENTS.md`, `CoWork Planning/yelp_project/docs/intern/README.md`
  - Do: Create the two dedicated showcase docs inside `.gsd/feature-plans/showcase-system/`; map Track A/B/C/D/E to prediction/surfacing/monitoring/onboarding/accountability using exported summaries and manifests; keep blocker truth explicit (`existing=6`, `missing=109`, Track D blocked by `outputs/tables/track_a_s5_candidate_splits.parquet`, Track E validity evidence metadata-only); define explainer triggers, required reading order, outputs, and guardrails using the prior-art intern docs; keep every statement inside the internal aggregate-safe, no-raw-review-text boundary.
  - Verify: `python - <<'PY'
from pathlib import Path
checks = {
    '.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md': ['prediction', 'surfacing', 'monitoring', 'onboarding', 'accountability', 'outputs/exports/eda/manifest.json', 'aggregate-safe', 'internal', 'track_a', 'track_b', 'track_c', 'track_d', 'track_e', 'outputs/tables/track_a_s5_candidate_splits.parquet', 'metadata-only'],
    '.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md': ['When to invoke', 'Inputs', 'Outputs', 'Guardrails', 'glossary', 'raw review text', 'CoWork Planning/yelp_project/docs_agent/AGENTS.md', 'CoWork Planning/yelp_project/docs/intern/README.md'],
}
for raw_path, markers in checks.items():
    text = Path(raw_path).read_text(encoding='utf-8')
    for marker in markers:
        assert marker in text, (raw_path, marker)
print('S04 docs contain required markers')
PY`
  - Done when: Both dedicated docs exist under `.gsd/feature-plans/showcase-system/` and they can stand alone as the honest content contract for later showcase and intern-facing work.
- [x] **T02: Link the showcase lane to the new docs and lock them with pytest** `est:45m`
  - Why: The new docs only help later agents if the canonical showcase plan surfaces point to them and automated regression coverage fails when those links or contract markers drift.
  - Files: `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`, `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md`, `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md`, `tests/test_trust_narrative_workflow.py`, `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`, `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`
  - Do: Update the existing showcase feature, sprint, and phase docs so they cite the new trust narrative and explainer workflow as the S04 content contract; preserve S03 guardrails about export-driven local hosting and no live parquet/DuckDB reads; add `tests/test_trust_narrative_workflow.py` with assertions for file existence, required trust-function markers, export-boundary language, blocker truth, intern explainer triggers/inputs/outputs/guardrails, and cross-links from the canonical showcase docs.
  - Verify: `python -m pytest tests/test_trust_narrative_workflow.py`
  - Done when: A fresh agent can discover the S04 docs from the showcase lane alone, and the dedicated pytest file fails if the narrative/workflow content or required cross-links drift.

## Files Likely Touched

- `.gsd/feature-plans/showcase-system/TRUST_NARRATIVE.md`
- `.gsd/feature-plans/showcase-system/INTERN_EXPLAINER_WORKFLOW.md`
- `.gsd/feature-plans/showcase-system/FEATURE_PLAN.md`
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/SPRINT.md`
- `.gsd/feature-plans/showcase-system/sprints/SPRINT-01-local-showcase-foundation/phases/PHASE-01-export-driven-experience-map.md`
- `tests/test_trust_narrative_workflow.py`
