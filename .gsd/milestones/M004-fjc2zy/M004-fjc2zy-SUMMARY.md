---
id: M004-fjc2zy
provides:
  - Local-hosted Next.js showcase runtime with executive-first + track drill-down IA, driven entirely by generated static artifacts.
  - Canonical report/deck generation from the same story/evidence contracts as the site, plus fail-closed parity diagnostics.
  - One-command integrated demo gate with smoke, parity, governance, and no-live-query enforcement.
key_decisions:
  - Keep blocked upstream evidence visible (not hidden) and treat explicit diagnostics as valid continuity behavior in stripped worktrees.
  - Use one canonical contract chain (`intake -> story -> tracks -> deliverables`) across website, report, deck, and verification gates.
patterns_established:
  - Contract-first showcase publishing with deterministic fallback semantics and machine-readable diagnostics.
  - Fail-closed integration verification via a phase-based demo gate that always writes a structured report.
observability_surfaces:
  - outputs/showcase/intake/{manifest.json,validation_report.json}
  - outputs/showcase/story/{sections.json,validation_report.json,tracks.json,tracks_validation_report.json}
  - outputs/showcase/deliverables/{showcase_report.md,showcase_deck.md,parity_report.json}
  - outputs/showcase/verification/demo_gate_report.json
  - scripts/run_showcase_demo_gate.py
requirement_outcomes:
  - id: R011
    from_status: active
    to_status: validated
    proof: M004 S05 integrated gate reruns passed in this closeout unit (`python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json`), with `gate_passed=true` and 6/6 phases passing; frontend tests/build and smoke checks all passed in the same report.
  - id: R012
    from_status: active
    to_status: validated
    proof: `outputs/showcase/deliverables/parity_report.json` shows `parity_passed=true` with 5/5 checks passing (`section_order`, `evidence_keys`, `pointer_fields`, `requirement_keys`, `governance_markers`), and S05 integrated gate enforces this parity phase fail-closed.
duration: ~31h44m slice execution + milestone closeout verification
verification_result: passed
completed_at: 2026-03-25
---

# M004-fjc2zy: Local showcase, report, and presentation system

**M004 delivered a demo-ready local showcase stack where website, report, and deck are generated from one canonical evidence contract and validated by a one-command fail-closed gate.**

## What Happened

S01 established the intake-locked shell and readiness diagnostics contract. S02 added the executive trust-story route with canonical section ordering and evidence rows. S03 added track drill-down routes and canonical per-track evidence artifacts. S04 generated report/deck artifacts from the same story/track contracts and added machine-readable parity diagnostics. S05 integrated all prior outputs into one assembled verification command (`run_showcase_demo_gate`) with deterministic smoke lifecycle handling, governance marker assertions, and no-live-query enforcement.

Code-change verification passed as required: `git diff --stat HEAD $(git merge-base HEAD main) -- ':!.gsd/'` reported substantial non-`.gsd` implementation deltas (54 files, including `showcase/`, `src/showcase/`, `scripts/`, `tests/`, and docs). The stat appears as deletions because of diff direction, but it confirms real code delivery rather than planning-only output.

## Cross-Slice Verification

### Success criteria verification

1. **One local command boots a Next.js showcase with real artifacts or explicit blocked states** — **met**.
   - Evidence: `python scripts/run_showcase_demo_gate.py ...` passed in this closeout unit with `gate_passed=true` and `runtime_smoke` phase passed.
   - `demo_gate_report.json` records blocked diagnostics surfaced (expected when upstream artifacts are missing) while gate remains passing.

2. **Executive-first trust narrative with track drill-down pages** — **met**.
   - Evidence: S02 delivered `/executive`; S03 delivered `/tracks` and `/tracks/[trackKey]`; smoke parity phase asserts route/section presence and canonical order.

3. **Major claims carry concrete evidence pointers** — **met**.
   - Evidence: S02/S03 established canonical evidence fields (`surface_key`, `path`, `reason`, `requirement_key`); parity report passed `pointer_fields` and `requirement_keys` checks.

4. **Report and deck generated from same canonical narrative/evidence contract as website** — **met**.
   - Evidence: S04 generators consume `sections.json` + `tracks.json`; parity report passed all 5 check classes with zero mismatches.

5. **Local demo verification proves assembled system without live analytics queries at request time** — **met**.
   - Evidence: S05 governance boundary phase in `demo_gate_report.json` shows `api_route_files=[]` and `live_query_violations=0`; frontend build/tests/smoke all pass in integrated flow.

6. **Governance boundaries remain visible/enforced (internal-only, aggregate-safe, no raw review text)** — **met**.
   - Evidence: governance markers check passed in parity report and integrated gate (`internal_only=true`, `aggregate_safe=true`, `raw_review_text_allowed=false`).

No success criteria were unmet.

### Definition-of-done verification

- Roadmap slice completion: verified all S01–S05 are `[x]` in `M004-fjc2zy-ROADMAP.md`.
- Slice summaries existence: verified `S01-SUMMARY.md` through `S05-SUMMARY.md` exist.
- Cross-slice integration: verified by passing integrated gate phase order (`build_artifacts -> parity -> frontend_test -> frontend_build -> runtime_smoke -> governance_boundary`) with all phases passed.
- Website static artifact-only behavior: verified by governance phase no-live-query checks and absence of `showcase/app/api/**` routes.
- Report/deck continuity: verified by parity report pass (5/5 checks).
- Local runbook/smoke path and explicit missing-artifact visibility: verified by runtime smoke pass with blocked diagnostics asserted.

## Requirement Changes

Validated transitions in M004:

- R011: **active -> validated** (proof in `requirement_outcomes` and S05 integrated gate evidence).
- R012: **active -> validated** (proof in `requirement_outcomes` and parity diagnostics evidence).

No other requirement statuses changed during this milestone closeout.

## Forward Intelligence

### What the next milestone should know
- Use `outputs/showcase/verification/demo_gate_report.json` as the first-stop truth surface for assembled showcase health.
- Use `outputs/showcase/deliverables/parity_report.json` as canonical cross-surface continuity evidence before making narrative edits.

### What's fragile
- Contract drift in evidence row fields (`surface_key`, `path`, `reason`, `requirement_key`) can silently break cross-surface continuity if parity checks are bypassed.
- Smoke/readiness behavior should preserve explicit blocked diagnostics; converting blocked states into hidden placeholders would break continuity semantics.

### Authoritative diagnostics
- `python scripts/run_showcase_demo_gate.py --config configs/showcase.yaml --base-url http://127.0.0.1:3000 --output outputs/showcase/verification/demo_gate_report.json`
- `outputs/showcase/deliverables/parity_report.json`

### What assumptions changed
- Initial assumption: complete upstream M001–M003 evidence would be present in this worktree.
- Actual outcome: upstream artifacts remain partially missing, and M004 correctly treats this as an explicitly blocked-but-demoable state with requirement-linked diagnostics.

## Files Created/Modified

- `.gsd/milestones/M004-fjc2zy/M004-fjc2zy-SUMMARY.md` — milestone closeout summary with criteria, DoD, and requirement transition verification.
- `.gsd/PROJECT.md` — updated to mark M004 as complete and reflect current project progression.
- `.gsd/KNOWLEDGE.md` — appended cross-cutting M004 closeout lessons for future milestones.
