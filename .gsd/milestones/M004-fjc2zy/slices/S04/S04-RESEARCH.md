# S04 Research — Report and deck generated from shared narrative/evidence source

## Summary
S04 is a **targeted integration slice**: S02/S03 already provide canonical runtime artifacts (`sections.json`, `tracks.json`) with requirement-linked evidence rows and blocked diagnostics. What is missing is a generation pipeline for report/deck plus parity proof that these deliverables consume the same story contract as the website.

Current state is favorable:
- Canonical executive order is already locked in `src/showcase/story_contract.py`.
- Canonical track order and section refs are already locked in `src/showcase/track_contract.py`.
- UI already renders those artifacts directly and smoke-checks parity for web routes.

Missing for S04:
- No report generator.
- No deck generator.
- No site/report/deck parity checker.
- No deliverable paths or runbook steps for report/deck outputs.

## Requirement focus (active requirements this slice owns/supports)
- **Primary owner:** **R012** (single coherent trust narrative across website/report/deck).
- **Direct support:** **R011** (showcase completeness now includes non-UI deliverables from same source).
- **Continuity support:** **R009**, **R010**, **R022** via preserved blocked/ready evidence rows and requirement keys in report/deck tables.
- **Governance continuity:** **R013** by carrying governance markers (`internal_only`, `aggregate_safe`, `raw_review_text_allowed=false`) into generated report/deck headers.

## Skill notes applied
- **react-best-practices**: apply `server-serialization` thinking to avoid duplicating large/derived narrative blobs in multiple places—generate once, consume many.
- **article-writing** (installed): use it for polishing wording only after contract fields are fixed; do not let prose become a second source of truth.
- **frontend-slides** (installed): useful for visual polish later, but S04 should first establish deterministic deck source generation and parity checks.

## Skill discovery (suggest)
Already installed and relevant:
- `article-writing`
- `frontend-slides`

Not installed but directly useful if deck export automation is chosen:
- Marp-focused skill (highest adoption):
  - `npx skills add softaworks/agent-toolkit@marp-slide`
- Pandoc-focused skill (if DOCX/PDF conversion is preferred):
  - `npx skills add terrylica/cc-skills@pandoc-pdf-generation`

## Library docs notes (Context7)
- `@marp-team/marp-cli` supports markdown deck conversion to HTML/PDF/PPTX and works via CLI (`npx @marp-team/marp-cli ...`).
- This fits S04 if deck source is generated as Markdown first and exported optionally during verification.

## Implementation landscape (files that exist and what they do)
- `configs/showcase.yaml`
  - Canonical section and track mappings already defined; no report/deck output schema yet.
- `src/showcase/story_contract.py`
  - Generates `outputs/showcase/story/sections.json` with canonical section order + evidence diagnostics.
- `src/showcase/track_contract.py`
  - Generates `outputs/showcase/story/tracks.json` with canonical track order + evidence diagnostics + section refs.
- `scripts/build_showcase_intake.py`, `scripts/build_showcase_story.py`, `scripts/build_showcase_tracks.py`
  - Existing build pipeline pattern (argparse CLI + deterministic JSON outputs).
- `scripts/showcase_smoke_check.py`
  - Parity checker exists for web routes only; no report/deck parity checks.
- `docs/showcase_local_runbook.md`
  - Stops at intake/story/tracks + web smoke; no report/deck generation steps.
- `showcase/lib/load-story.ts`, `showcase/lib/load-tracks.ts`
  - Runtime consumers already tied to canonical artifacts; should remain unchanged in S04 unless adding navigation links to generated docs.

## Natural seams for planner decomposition
1. **Shared narrative source seam (contract extension)**
   - Introduce a single derived narrative artifact for non-UI deliverables (or explicitly standardize on existing `sections.json` + `tracks.json` as inputs).
   - Keep claim IDs/evidence anchors deterministic and requirement-keyed.

2. **Report generator seam**
   - New Python CLI (pattern-matched with existing `build_showcase_*` scripts) to emit `report.md` from canonical artifacts.
   - Include executive section ordering first, then track drill-down appendix.

3. **Deck generator seam**
   - New CLI to emit deck source markdown (Marp-compatible recommended) from the same claim/evidence rows.
   - Optional export step (PDF/PPTX) should be operational, not required for contract logic.

4. **Parity verification seam**
   - New script/test(s) that assert report/deck contain the same ordered section keys and evidence keys as website source artifacts.
   - This is the key anti-drift proof for R012.

5. **Runbook + observability seam**
   - Extend `docs/showcase_local_runbook.md` with report/deck build + parity commands.
   - Emit machine-readable parity result JSON for S05 consumption.

## What to build/prove first
1. **Parity contract first**: define exactly what “same story” means (section order, claim/evidence IDs, requirement keys, governance markers).
2. **Report/deck generation second**: both must read the same canonical artifact(s), not each other.
3. **Parity checker third**: fail fast when report/deck drift from story/tracks artifacts.
4. **Optional conversion last**: PDF/PPTX rendering is packaging, not narrative truth.

## Key risks / constraints
- **Biggest risk:** prose-first authoring that bypasses artifact contract and reintroduces manual drift.
- **Format risk:** if deck is authored directly in slides tooling without generated markdown source, parity becomes brittle.
- **Governance drift risk:** report/deck omitting explicit internal/aggregate-safe markers would regress R013 continuity.
- **Evidence drift risk:** dropping blocked diagnostics in text deliverables would hide R009/R010/R022 continuity status.

## Verification plan (recommended)
```bash
# 1) Rebuild canonical inputs
python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake
python scripts/build_showcase_story.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --output outputs/showcase/story
python scripts/build_showcase_tracks.py --config configs/showcase.yaml --intake outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --output outputs/showcase/story

# 2) Build new S04 deliverables (expected new scripts)
python scripts/build_showcase_report.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables
python scripts/build_showcase_deck.py --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --output outputs/showcase/deliverables

# 3) Contract/parity tests (expected new tests)
python -m pytest tests/test_showcase_report_contract.py tests/test_showcase_deck_contract.py tests/test_showcase_parity_contract.py -q

# 4) Optional deck export proof (if Marp path chosen)
npx @marp-team/marp-cli outputs/showcase/deliverables/showcase_deck.md --html -o outputs/showcase/deliverables/showcase_deck.html

# 5) Keep existing website parity gate green
npm --prefix showcase run test -- --run
npm --prefix showcase run build
python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --story outputs/showcase/story/sections.json --tracks outputs/showcase/story/tracks.json --base-url http://127.0.0.1:3000
```

## Recommendation
Treat S04 as a **continuity-contract slice**, not a design slice:
- generate report + deck from canonical story/track artifacts,
- preserve requirement-linked evidence rows (including blocked diagnostics),
- add explicit parity assertions so drift is caught automatically,
- then optionally layer slide rendering/export tooling.

That gives S05 a reliable handoff: one narrative source, three surfaces (site/report/deck), one verification story.
