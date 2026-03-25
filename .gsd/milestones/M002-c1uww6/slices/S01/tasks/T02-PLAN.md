---
estimated_steps: 4
estimated_files: 11
skills_used:
  - coding-standards
  - verification-loop
---

# T02: Scaffold the shared modeling package and output contract

**Slice:** S01 — Repo-state reconciliation and shared modeling contract
**Milestone:** M002-c1uww6

## Description

Create the shared `src/modeling/` and `outputs/modeling/` surface that all later baseline slices will use. This task establishes the package/output contract before Track A–D implementation begins so later work cannot drift into ad hoc layouts.

## Steps

1. Create the `src/modeling/` package root plus `common`, `track_a`, `track_b`, `track_c`, and `track_d` subpackages.
2. Create `outputs/modeling/track_a` through `outputs/modeling/track_d` directories.
3. Document the required artifact bundle and summary contract in `src/modeling/README.md`.
4. Verify the scaffold exists and is easy for a future agent to discover.

## Must-Haves

- [ ] `src/modeling/` exists with explicit subpackages for `common`, `track_a`, `track_b`, `track_c`, and `track_d`.
- [ ] `outputs/modeling/track_a` through `outputs/modeling/track_d` exist as the canonical output roots.
- [ ] `src/modeling/README.md` explains the required artifact bundle and summary contents.

## Verification

- `test -d src/modeling/common && test -d src/modeling/track_a && test -d src/modeling/track_b && test -d src/modeling/track_c && test -d src/modeling/track_d`
- `test -d outputs/modeling/track_a && test -d outputs/modeling/track_b && test -d outputs/modeling/track_c && test -d outputs/modeling/track_d && test -f src/modeling/README.md`

## Inputs

- `.gsd/milestones/M002-c1uww6/M002-c1uww6-CONTEXT.md` — milestone contract that defines what the modeling scaffold must support
- `.gsd/milestones/M002-c1uww6/M002-c1uww6-ROADMAP.md` — slice and artifact expectations that the scaffold must honor

## Expected Output

- `src/modeling/__init__.py` — shared modeling package root
- `src/modeling/common/__init__.py` — future shared helpers package
- `src/modeling/track_a/__init__.py` — Track A baseline package root
- `src/modeling/track_b/__init__.py` — Track B baseline package root
- `src/modeling/track_c/__init__.py` — Track C baseline package root
- `src/modeling/track_d/__init__.py` — Track D baseline package root
- `src/modeling/README.md` — shared artifact and summary contract
- `outputs/modeling/track_a/.gitkeep` — Track A output root placeholder
- `outputs/modeling/track_b/.gitkeep` — Track B output root placeholder
- `outputs/modeling/track_c/.gitkeep` — Track C output root placeholder
- `outputs/modeling/track_d/.gitkeep` — Track D output root placeholder

## Observability Impact

- New signals: the presence of `src/modeling/` subpackages, the canonical `outputs/modeling/<track>/` roots, and the artifact-contract narrative in `src/modeling/README.md`
- How to inspect: run the task verification shell checks, inspect `src/modeling/README.md`, and use `python -m pytest tests/test_m002_modeling_contract.py` to see the shared contract status
- Failure visibility: missing package roots, missing output roots, or a missing README contract now fail through explicit path checks instead of surfacing later as ad hoc downstream layout drift
