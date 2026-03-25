---
estimated_steps: 4
estimated_files: 4
skills_used:
  - verification-loop
---

# T01: Reconcile M002 planning with live repo state

**Slice:** S01 — Repo-state reconciliation and shared modeling contract
**Milestone:** M002-c1uww6

## Description

Refresh the M002 planning surface so it reflects the current worktree instead of inherited M001 assumptions. This task closes the stale-blocker problem before any modeling code or output scaffolding is introduced.

## Steps

1. Inspect current curated inputs and key Track A–D EDA artifacts that affect milestone sequencing.
2. Compare those live surfaces with the M002 context and roadmap language.
3. Update any stale wording about missing artifacts, Track D Stage 5 blocking, or current starting conditions.
4. Re-run mechanical checks to prove the milestone docs now match repo truth.

## Must-Haves

- [ ] M002 docs explicitly acknowledge the current worktree state for curated inputs and key Track A–D artifacts.
- [ ] M002 docs preserve the scope lock: D1 required, D2 optional, Track A preferred as the default M003 audit target.

## Verification

- `python - <<'PY'
from pathlib import Path
required = [
    Path('data/curated/review_fact.parquet'),
    Path('data/curated/review_fact_track_b.parquet'),
    Path('data/curated/review.parquet'),
    Path('data/curated/business.parquet'),
    Path('data/curated/user.parquet'),
    Path('data/curated/snapshot_metadata.json'),
    Path('outputs/tables/track_a_s5_candidate_splits.parquet'),
]
missing = [p.as_posix() for p in required if not p.exists()]
assert not missing, missing
print('repo-state truth inputs/artifacts present')
PY`
- `python - <<'PY'
from pathlib import Path
text = Path('.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md').read_text(encoding='utf-8') + Path('.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md').read_text(encoding='utf-8')
for marker in ['current worktree', 'track_a_s5_candidate_splits.parquet', 'D1 required', 'D2 optional', 'Track A preferred']:
    assert marker in text, marker
print('milestone docs contain current-truth markers')
PY`

## Inputs

- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md` — current milestone context to align with repo truth
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` — current milestone roadmap to align with repo truth
- `data/curated/` — actual curated input surfaces that determine whether inherited blocker language is stale
- `outputs/tables/` — actual Track A–D EDA artifact state that determines real sequencing and blockers

## Expected Output

- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md` — updated current-truth milestone context
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` — updated current-truth milestone roadmap

## Observability Impact

- Signals changed: the milestone context and roadmap become the inspectable current-state contract for what curated inputs and Track A–D EDA artifacts already exist in the current worktree.
- How to inspect later: read `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md` and `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`, then run the verification snippets in this task to confirm the files and marker strings still match repo truth.
- Failure state made visible: if curated inputs disappear, key EDA artifacts go missing, or stale blocker language returns, the verification commands fail with explicit missing-path or missing-marker output.
