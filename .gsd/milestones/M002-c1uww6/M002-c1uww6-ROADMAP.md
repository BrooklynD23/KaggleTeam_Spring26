# M002-c1uww6: Baseline modeling by track

**Vision:** Turn the completed Yelp EDA layer into reproducible baseline modeling evidence for the trust-marketplace story — prediction, surfacing, monitoring, and onboarding — while keeping scope tight, outputs standardized, and downstream fairness/reporting handoff clean.

## Success Criteria

- The repo exposes one reproducible baseline result for Track A, Track B, Track C, and Track D1 with track-appropriate evaluation artifacts and summaries
- The milestone planning and execution surfaces reflect actual repo state rather than stale inherited blocker language from M001
- Every required track writes outputs into a stable modeling artifact contract under `outputs/modeling/` that later M003 and M004 work can consume without ad hoc cleanup
- Track C delivers measurable monitoring/drift evidence rather than vague narrative or forecasting creep
- Track D delivers a real D1 cold-start baseline against an explicit as-of popularity comparator without silently making D2 mandatory
- At least one upstream model is clearly documented as the preferred M003 fairness-audit target, with Track A preferred by default

## Current Worktree Baseline

- The current worktree already contains the curated inputs needed to start M002 baseline work: `data/curated/review_fact.parquet`, `data/curated/review_fact_track_b.parquet`, `data/curated/review.parquet`, `data/curated/business.parquet`, `data/curated/user.parquet`, and `data/curated/snapshot_metadata.json`.
- The current worktree already contains the Track A anchor artifact `outputs/tables/track_a_s5_candidate_splits.parquet`, plus Track B, Track C, and Track D EDA tables through their present summary/leakage surfaces.
- S01 therefore reconciles milestone docs and standardizes the modeling contract; it does not need to wait on missing upstream EDA deliverables or treat Track D as presently blocked on Track A Stage 5 in this worktree.
- Scope lock remains explicit for execution sequencing and later audit planning: D1 required, D2 optional, Track A preferred as the default M003 fairness-audit target.

## Key Risks / Unknowns

- Stale planning-state mismatch — inherited M001 planning docs can still mis-sequence work if they are not reconciled against the current worktree truth above
- Track C ambiguity — if monitoring outputs are not concretely defined, the lane can collapse into prose-only summary work or expand into forecasting scope that the milestone does not need
- Track D scope creep — if D2 is allowed to drift from optional to implicit requirement, the milestone can absorb unnecessary recommender complexity and miss the semester-safe path
- Artifact drift — if each track emits different output shapes or locations, M003 audit work and M004 reporting/showcase work inherit cleanup instead of usable evidence
- Track B overengineering — if the team jumps to pairwise/listwise learning before securing a pointwise ranking baseline, time goes to sophistication rather than proof

## Proof Strategy

- Stale planning-state mismatch → retire in S01 by proving the milestone plan, blockers, and current-state assumptions match live repo surfaces under `data/curated/` and `outputs/tables/`
- Track C ambiguity → retire in S04 by proving Track C emits measurable drift/stability artifacts, a ranked change surface, and an interpretable figure with explicit monitoring framing
- Track D scope creep → retire in S05 by proving D1 completes independently against an as-of popularity baseline and that any D2 work remains explicitly optional and separately reported
- Artifact drift → retire in S01 and S06 by proving a standard modeling artifact contract exists first and is then populated consistently across Tracks A, B, C, and D1
- Track B overengineering → retire in S03 by proving a pointwise scoring baseline can beat trivial comparators under grouped ranking evaluation without needing a heavier ranking stack

## Verification Classes

- Contract verification: artifact existence checks, summary-content checks, metrics-file checks, config snapshot checks, and path/structure checks under `src/modeling/` and `outputs/modeling/`
- Integration verification: real execution of Track A, Track B, Track C, and Track D1 baseline entrypoints against curated inputs and existing EDA-derived surfaces
- Operational verification: local-only baseline workflow execution and rerun verification; no cloud deployment required, with compute escalation to Colab Pro or HPC only if local execution is proven insufficient
- UAT / human verification: review of milestone summaries and figures for interpretability and story coherence across prediction, surfacing, monitoring, and onboarding

## Milestone Definition of Done

This milestone is complete only when all are true:

- all slice deliverables are complete
- S01 has reconciled stale planning assumptions against actual repo state
- Track A has a leakage-safe temporal baseline with MAE/RMSE and a naïve comparator
- Track B has a snapshot-only usefulness baseline evaluated with NDCG@10 within age-controlled groups and compared against trivial baselines
- Track C has a measurable monitoring baseline with explicit drift/stability evidence and no forecasting claims
- Track D1 has a cold-start baseline evaluated against an as-of popularity baseline with Recall@20/NDCG@10
- every required track has produced the standard artifact bundle under `outputs/modeling/<track>/`
- any D2 work is explicitly marked optional, reported separately, and remains non-blocking
- a preferred M003 fairness-audit target is documented, with Track A preferred by default
- final integrated milestone outputs can be consumed downstream without cleanup archaeology

## Requirement Coverage

- Covers: R005, R006, R007, R008
- Partially covers: R009, R012
- Leaves for later: R010, R011, R020, R021, R022
- Orphan risks: none

## Slices

- [x] **S01: Repo-state reconciliation and shared modeling contract** `risk:high` `depends:[]`
  > After this: the team can point to a current-truth M002 execution contract with stale blockers removed, per-track baseline definitions locked, and a standard artifact structure ready for implementation.

- [x] **S02: Track A temporal baseline and audit-target handoff** `risk:high` `depends:[S01]`
  > After this: the repo exposes a real future-star baseline for Track A with MAE/RMSE, a naïve comparator, and a summary strong enough to serve as the default M003 audit target.

- [x] **S03: Track B snapshot ranking baseline** `risk:medium` `depends:[S01]`
  > After this: the repo exposes a pointwise usefulness baseline evaluated as age-controlled ranking within valid groups, with NDCG@10 and trivial comparators reported.

- [x] **S04: Track C monitoring baseline** `risk:medium` `depends:[S01]`
  > After this: the repo exposes measurable drift/monitoring artifacts for Track C — including drift or stability metrics, a ranked change surface, and an interpretable figure — without drifting into forecasting scope.

- [x] **S05: Track D1 cold-start baseline with optional D2 gate** `risk:medium` `depends:[S01,S02]`
  > After this: the repo exposes a D1 cold-start baseline against an explicit as-of popularity comparator, while any D2 work remains clearly optional and separately reported.

- [x] **S06: Integrated modeling handoff and milestone verification** `risk:medium` `depends:[S02,S03,S04,S05]`
  > After this: Tracks A, B, C, and D1 (required) are verified together under one modeling artifact contract, D2 remains optional/non-blocking, the preferred M003 audit target is explicit, and downstream reporting/showcase work has a clean handoff surface.

## Boundary Map

### S01 → S02

Produces:
- current-truth milestone assumptions for curated inputs, EDA artifact availability, and real remaining blockers
- agreed Track A baseline contract: allowed inputs, prohibited features, primary metrics, comparator, and output bundle
- shared modeling directory and artifact conventions under `src/modeling/` and `outputs/modeling/`

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- agreed Track B baseline contract: pointwise scoring baseline, grouped ranking evaluation, NDCG@10 target, and trivial comparators
- shared summary/metrics/config artifact conventions
- explicit rule that M002 does not require pairwise/listwise ranking

Consumes:
- nothing (first slice)

### S01 → S04

Produces:
- agreed Track C baseline contract: monitoring-only framing, required drift/stability artifacts, required ranked change surface, and required interpretable figure
- explicit rule that Track C completion cannot rest on prose alone

Consumes:
- nothing (first slice)

### S01 → S05

Produces:
- agreed Track D scope contract: D1 required, D2 optional/stretch
- explicit D1 comparator and metric contract
- explicit rule that D2 cannot become a milestone-completion dependency

Consumes:
- nothing (first slice)

### S02 → S05

Produces:
- stable Track A temporal split and baseline summary surfaces that Track D planning can treat as upstream truth
- preferred default M003 audit-target surface if Track A lands cleanly

Consumes from S01:
- current-truth assumptions and shared artifact contract

### S02 → S06

Produces:
- Track A modeling outputs under `outputs/modeling/track_a/`
- a baseline summary that names inputs, excluded features, comparator, metrics, limitations, and audit suitability

Consumes from S01:
- shared modeling contract and milestone assumptions

### S03 → S06

Produces:
- Track B modeling outputs under `outputs/modeling/track_b/`
- ranking metrics and grouped evaluation evidence suitable for downstream narrative and reporting

Consumes from S01:
- shared modeling contract and Track B scope ceiling

### S04 → S06

Produces:
- Track C monitoring outputs under `outputs/modeling/track_c/`
- measurable drift/stability evidence and interpretable monitoring summaries that can slot into the trust-marketplace story

Consumes from S01:
- shared modeling contract and Track C monitoring-only framing

### S05 → S06

Produces:
- Track D1 modeling outputs under `outputs/modeling/track_d/`
- explicit D1 comparator results and, if attempted, separately labeled D2 stretch outputs

Consumes from S01:
- shared modeling contract and D1-required / D2-optional scope lock

Consumes from S02:
- upstream Track A truth needed for clean downstream reasoning and story alignment
