# S01: Repo-state reconciliation and shared modeling contract

**Goal:** Reconcile M002 planning against actual repo state, then establish the shared modeling package/output contract that every baseline slice will use.
**Demo:** A fresh agent can inspect the repo and see a current-truth M002 contract, a standardized `src/modeling/` / `outputs/modeling/` surface, and executable verification checks proving stale blocker language has been retired.

## Must-Haves

- The slice replaces stale inherited blocker/status assumptions with repo-grounded truth for curated inputs, key A–D EDA artifacts, and remaining real blockers.
- The repo contains a standardized modeling scaffold and documented artifact contract for Tracks A, B, C, and D before per-track implementation begins.
- Regression or shell verification checks prove the shared modeling surface exists and the milestone contract can be re-checked mechanically.
- The slice makes Track D scope lock explicit: D1 required, D2 optional/stretch, Track A preferred as the default M003 audit target.

## Proof Level

- This slice proves: contract
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `test -f .gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md && test -f .gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md && rg -n "D1 required|D2 optional|Track A preferred" .gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md .gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`
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
print({'required_count': len(required), 'missing': missing})
assert not missing, missing
print('repo-state truth inputs/artifacts present')
PY`
- `test -d src/modeling/common && test -d src/modeling/track_a && test -d src/modeling/track_b && test -d src/modeling/track_c && test -d src/modeling/track_d && test -d outputs/modeling/track_a && test -d outputs/modeling/track_b && test -d outputs/modeling/track_c && test -d outputs/modeling/track_d`
- `python -m pytest tests/test_m002_modeling_contract.py`

## Observability / Diagnostics

- Runtime signals: current-state contract file under `.gsd/milestones/M002-c1uww6/` plus modeling-contract assertions in `tests/test_m002_modeling_contract.py`
- Inspection surfaces: `M002-c1uww6-CONTEXT.md`, `M002-c1uww6-ROADMAP.md`, `src/modeling/`, `outputs/modeling/`, and `python -m pytest tests/test_m002_modeling_contract.py`
- Failure visibility: missing curated inputs, missing shared modeling directories, or stale milestone language failing contract assertions
- Redaction constraints: no raw review text or row-level examples in milestone or contract artifacts

## Integration Closure

- Upstream surfaces consumed: `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`, `data/curated/`, `outputs/tables/`, `configs/track_a.yaml`, `configs/track_b.yaml`, `configs/track_c.yaml`, `configs/track_d.yaml`
- New wiring introduced in this slice: shared modeling scaffold under `src/modeling/` and `outputs/modeling/` plus a repo-state/modeling-contract regression test
- What remains before the milestone is truly usable end-to-end: per-track baseline implementation and integrated milestone verification in S02–S06

## Tasks

- [x] **T01: Reconcile M002 planning with live repo state** `est:45m`
  - Why: Later slices should not inherit stale blocker language or partial-repo assumptions that no longer match this worktree.
  - Files: `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`, `data/curated/`, `outputs/tables/`
  - Do: Compare the milestone artifacts against actual curated inputs and key Track A–D EDA outputs; add explicit current-truth language where needed; remove or override stale assumptions about missing artifacts and Track D Stage 5 blocking in the M002 planning surface.
  - Verify: `python - <<'PY'
from pathlib import Path
text = Path('.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md').read_text(encoding='utf-8') + Path('.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md').read_text(encoding='utf-8')
for marker in ['track_a_s5_candidate_splits.parquet', 'current worktree', 'D1 required', 'D2 optional']:
    assert marker in text, marker
print('milestone docs contain current-truth markers')
PY`
  - Done when: the milestone docs clearly distinguish current repo truth from inherited M001 assumptions and no longer imply Track D is presently blocked on Stage 5 in this worktree.
- [x] **T02: Scaffold the shared modeling package and output contract** `est:1h`
  - Why: Tracks A–D need one agreed code/output surface before any baseline implementation begins, or downstream slices will drift into ad hoc layouts.
  - Files: `src/modeling/__init__.py`, `src/modeling/common/__init__.py`, `src/modeling/track_a/__init__.py`, `src/modeling/track_b/__init__.py`, `src/modeling/track_c/__init__.py`, `src/modeling/track_d/__init__.py`, `src/modeling/README.md`, `outputs/modeling/track_a/.gitkeep`, `outputs/modeling/track_b/.gitkeep`, `outputs/modeling/track_c/.gitkeep`, `outputs/modeling/track_d/.gitkeep`
  - Do: Create the shared `src/modeling/` package structure and `outputs/modeling/` track folders; document the required artifact bundle, summary contents, and per-track contract in `src/modeling/README.md`; keep the scaffold boring and explicit rather than speculative.
  - Verify: `test -d src/modeling/common && test -d src/modeling/track_a && test -d src/modeling/track_b && test -d src/modeling/track_c && test -d src/modeling/track_d && test -f src/modeling/README.md && test -d outputs/modeling/track_a && test -d outputs/modeling/track_b && test -d outputs/modeling/track_c && test -d outputs/modeling/track_d`
  - Done when: a fresh agent can inspect `src/modeling/README.md` and the scaffolded directories and understand exactly where M002 code and outputs belong.
- [x] **T03: Add shared modeling-contract verification** `est:45m`
  - Why: S01 should fail loudly if the modeling scaffold or milestone scope contract drifts before per-track slices begin.
  - Files: `tests/test_m002_modeling_contract.py`, `src/modeling/README.md`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md`, `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`
  - Do: Add a focused regression test that asserts the shared modeling directories exist, the milestone docs preserve the D1-required/D2-optional scope lock, Track A is named as the preferred audit target, and the artifact contract markers remain present.
  - Verify: `python -m pytest tests/test_m002_modeling_contract.py`
  - Done when: the repo has a mechanical check for the M002 shared contract and future edits can no longer silently drift away from the agreed baseline scope.

## Files Likely Touched

- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md`
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md`
- `src/modeling/__init__.py`
- `src/modeling/common/__init__.py`
- `src/modeling/track_a/__init__.py`
- `src/modeling/track_b/__init__.py`
- `src/modeling/track_c/__init__.py`
- `src/modeling/track_d/__init__.py`
- `src/modeling/README.md`
- `outputs/modeling/track_a/.gitkeep`
- `outputs/modeling/track_b/.gitkeep`
- `outputs/modeling/track_c/.gitkeep`
- `outputs/modeling/track_d/.gitkeep`
- `tests/test_m002_modeling_contract.py`
