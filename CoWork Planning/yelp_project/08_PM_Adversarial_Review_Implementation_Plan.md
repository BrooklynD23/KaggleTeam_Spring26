# PM Review Report: Adversarial Review of Implementation Plan

> **SUPERSEDED — DO NOT USE FOR IMPLEMENTATION DECISIONS**
>
> All 7 findings in this document have been resolved in [`09_Resolution_TrackA_TrackB_Implementation_Plan.md`](09_Resolution_TrackA_TrackB_Implementation_Plan.md). That document is the authoritative source of truth for Track A / Track B contract decisions, leakage policy, validation requirements, and subagent ownership rules.
>
> This file is retained as a historical audit trail only. Agents and implementers must not act on the recommendations below — refer to document 09 instead.

**Date:** 2026-03-10
**Reviewed Artifact:** `yelp_project/07_Implementation_Plan_Ingestion_TrackA_TrackB.md`
**Reviewer:** Codex
**Recommendation:** ~~Do not approve the plan as-is. Revise the critical and high-severity items before implementation begins.~~ **Resolved — see document 09.**

## Executive Summary

The implementation plan is directionally strong, but it still contains several failure modes that would either break ingestion, invalidate Track A's as-of methodology, or overstate Track B readiness.

One correction since the initial review: photo data is now present under `Dataset(Raw)`, but it is present as a separate raw archive at `Dataset(Raw)/Yelp Photos/yelp_photos.tar`, not inside `Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar`. That changes the original concern from "missing photo data" to "photo ingestion path mismatch." The plan still needs to be updated if photo support is intended.

## Current Approval Status

**Status:** Not ready for PM approval

Blocking issues:

1. Track A still allows post-hoc snapshot fields to leak into historical rows.
2. Track A as-of logic invents intra-day ordering and conflicts with its own leakage audit.
3. Photo ingestion is not wired to the current raw-data layout if photo is in scope.
4. Track B feasibility and leakage checks are weaker than the plan claims.

## Findings

### 1. Critical: Shared `review_fact` leaks snapshot-only fields into Track A

**What is wrong**

The shared curated table includes `b.is_open`, `u.fans`, and `u.elite` for every historical review row. Those are snapshot-time fields, not guaranteed as-of features at review time. Track A's stated rule is stricter: every feature for a review at time `t` must use only information available before `t`.

**Why PM should care**

This can invalidate the central promise of Track A: strict temporal evaluation without future leakage. Even if the team avoids the obvious lifetime aggregates, the current shared table still leaves a path for using future-derived metadata in EDA or later modeling.

**Evidence**

- Plan includes snapshot fields in `review_fact`: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 486-497
- Plan only bans four lifetime aggregates: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` line 513
- Track A requires strict as-of semantics: `track_a/AGENTS.md` line 24 and `track_a/CLAUDE.md` line 26

**PM action**

Require one of these before approval:

- Split the curated layer into a Track A-safe view and a Track B snapshot view
- Add an explicit Track A feature allowlist and ban `is_open`, `fans`, `elite`, and any other snapshot-only fields
- Expand the leakage audit to check for all non-as-of fields, not just the four current aggregates

### 2. Critical: Track A as-of history invents same-day order and disagrees with the audit

**What is wrong**

The plan says prior-history features should use reviews strictly before the current review's date, but the SQL orders by `review_date, review_id` and uses `1 PRECEDING`. That creates an artificial within-day order even though the dataset only exposes dates, not timestamps.

The leakage audit later checks prior counts using `rf2.review_date < rf.review_date`, which is stricter than the as-of table logic. The plan therefore disagrees with itself.

**Why PM should care**

This is a methodology problem, not just an implementation detail. If same-day multi-review activity exists, the plan can either:

- leak same-day information into "prior" features, or
- fail its own leakage audit

Either outcome undermines trust in Track A.

**Evidence**

- User-history SQL and rationale: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 624-648
- Leakage audit comparison uses strict earlier dates: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 904-909

**PM action**

Require a single policy and enforce it everywhere:

- safest option: prior history must be strictly from earlier dates only
- alternative: aggregate at user-day and business-day first, then lag by one full day

### 3. High: Photo data exists, but the plan still points to the wrong raw-data path

**What is wrong**

Photo data is now present locally, but the plan still assumes it will be extracted from `Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar`. The current raw layout shows a separate asset path: `Dataset(Raw)/Yelp Photos/yelp_photos.tar`.

**Why PM should care**

If photo is meant to stay in scope, the current plan will still fail or silently omit it because the extraction and ingestion path are wrong for the current dataset layout.

**Evidence**

- Current raw assets observed locally:
  - `Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar`
  - `Dataset(Raw)/Yelp Photos/yelp_photos.tar`
- Plan still expects `photo` in the main JSON flow: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 86, 106, 241, 361, 1626

**PM action**

Pick one and make it explicit:

- Add a second extraction branch for the separate photo tar
- Mark photo as out of scope for Track A and Track B and remove it from the shared ingestion contract

### 4. High: Track B pairwise-feasibility math overstates usable training signal

**What is wrong**

The query says it counts valid pairs with different `useful` values, but the SQL only computes `C(n,2)` from group size. It never subtracts tied pairs.

**Why PM should care**

Track B uses this step to decide whether pairwise ranking is feasible. Because `useful` is heavily zero-inflated and tie-heavy, this query can materially overestimate the amount of usable pairwise supervision.

**Evidence**

- Pairwise query comment vs. SQL mismatch: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 1418-1425
- Track B stage definition expects valid pairwise-comparison counts: `track_b/03_EDA_Pipeline_Track_B_Usefulness_Ranking.md` line 187

**PM action**

Require tied-pair subtraction before feasibility sign-off. The gate should be based on non-tied comparisons, not raw combinations.

### 5. High: Track B leakage/scope check is mostly a checklist, not a real validation stage

**What is wrong**

The proposed `run_track_b_scope_checks()` function only emits canned reminders. It does not inspect feature tables, artifacts, or label construction outputs. The only automated SQL shown checks whether `age_bucket` is null.

**Why PM should care**

The stage is presented as a safety gate, but it would not actually catch:

- `funny` or `cool` sneaking into features
- labels computed across age buckets
- row-level output leakage
- unsupported temporal claims in derived outputs

**Evidence**

- Static checklist implementation: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 1478-1538
- Weak automated query: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 1544-1549
- Track B spec expects actual checks for these conditions: `track_b/03_EDA_Pipeline_Track_B_Usefulness_Ranking.md` lines 199-203

**PM action**

Require a real validation stage that queries generated tables and inspects declared feature columns or manifests.

### 6. Medium: Track A first-review bucketing is wrong

**What is wrong**

The Stage 3 history-depth bucketing logic assumes first reviews have `NULL` prior counts. But `COUNT(*) OVER (... 1 PRECEDING)` yields `0`, not `NULL`. Those rows therefore fall through the `CASE` statement incorrectly.

**Why PM should care**

This will distort a core EDA output used to reason about sparsity and cold-start behavior.

**Evidence**

- Prior-count window: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 625-629
- Buggy bucket mapping: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 687-691

**PM action**

Change the first bucket to `WHEN user_prior_review_count = 0 THEN '0 (first review)'`.

### 7. Medium: The plan tolerates silent row loss from the shared inner joins

**What is wrong**

The design says row-count equality must be verified or the delta documented, but the implementation only logs a warning and keeps going if `review_fact` has fewer rows than `review`.

**Why PM should care**

If the joins drop rows, downstream counts, split sizes, and as-of statistics are all computed on a filtered population. That is acceptable only if the delta is intentionally approved and documented.

**Evidence**

- Design intent: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` line 515
- Current implementation only warns: `07_Implementation_Plan_Ingestion_TrackA_TrackB.md` lines 1853-1860

**PM action**

Treat any non-zero drop as a review gate, not an informational warning.

## Recommended PM Decision

Approve only after a revision that does all of the following:

1. Separates Track A-safe as-of features from Track B snapshot features.
2. Fixes same-day prior-history semantics and aligns the leakage audit with that rule.
3. Updates photo ingestion to match the current raw-data layout, or removes photo from the shared ingestion contract.
4. Replaces Track B's pairwise-feasibility and leakage-check placeholders with actual validation logic.
5. Fixes the first-review bucketing bug and promotes row-loss warnings to hard validation gates.

## Suggested PM Follow-Up Questions

1. Is photo actually in scope for Track A and Track B, or should it be removed from the shared ingestion contract?
2. Does the team want a single shared curated table, or separate Track A and Track B curated views with different leakage rules?
3. What is the approval criterion for row drops during `review_fact` construction: zero tolerance, capped tolerance, or documented exception?

## Bottom Line

The plan is close, but it is not yet safe to treat as implementation-ready. The remaining issues are concentrated in leakage control, feasibility validation, and raw-data contract clarity rather than in the overall architecture choice.
