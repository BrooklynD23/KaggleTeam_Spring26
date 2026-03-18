# Resolution Memo: Track A / Track B Implementation Plan

**Version:** 1.1
**Date:** 2026-03-11
**Status:** Approved as a resolution memo; implementation remains blocked until the affected source documents are synced to this memo.
**Revision history:** v1.1 — expanded doc sync scope, closed direct-join escape hatch, specified Stage 7 scan, defined tied-pair semantics, strengthened verification, clarified DuckDB ownership, added prompt-override expiry.

---

## 1. Purpose

This memo resolves the remaining contract and implementation conflicts across the following planning artifacts:

- `07_Implementation_Plan_Ingestion_TrackA_TrackB.md`
- `08_PM_Adversarial_Review_Implementation_Plan.md`
- `track_a/AGENTS.md`
- `track_a/CLAUDE.md`
- `track_a/02_EDA_Pipeline_Track_A_Future_Ratings.md`
- `track_b/03_EDA_Pipeline_Track_B_Usefulness_Ranking.md`
- `track_b/AGENTS.md`
- `track_b/CLAUDE.md`

This document is a **standalone resolution artifact**, not a full replacement for the implementation plan. Its purpose is to lock the unresolved decisions that previously left implementers and subagents room to diverge.

**Execution rule:** Track A / Track B implementation must not start until the affected source docs are updated to match this memo.

---

## 2. Resolved Decisions

### 2.1 Shared curated-layer contract

The curated layer is split into two explicit artifacts:

1. `data/curated/review_fact.parquet`
   - This is the **Track A-safe** curated table.
   - It excludes lifetime aggregates and snapshot-only fields that violate strict as-of semantics.
   - It does not include raw review text.

2. `data/curated/review_fact_track_b.parquet`
   - This is the **Track B snapshot-enriched** curated table.
   - It may include snapshot-only fields needed by Track B's single-snapshot framing.

**Resolution:** Track A must never read from `review_fact_track_b`. Track B must use `review_fact_track_b.parquet` even where older docs still say `review_fact.parquet`.

### 2.2 Track A leakage policy

Track A remains a strict as-of task.

The following fields are banned from the Track A base table and from Track A feature construction unless an explicitly as-of version is computed:

- `business.stars`
- `business.review_count`
- `business.is_open`
- `user.average_stars`
- `user.review_count`
- `user.fans`
- `user.elite`

**Resolution:** `review_fact.parquet` is the enforceable Track A allowlisted base. Leakage checks must validate against all banned snapshot-only and lifetime aggregate fields, not only the original four aggregate fields.

**Direct-join constraint:** Track A stages that read raw entity Parquet files (e.g., `review.parquet` for text sampling in Stage 2) must not join or extract banned snapshot-only fields from any source. The ban applies regardless of whether the field is accessed via `review_fact_track_b.parquet`, raw entity files, or DuckDB views. Leakage audits must verify both output column names and code-level query paths.

### 2.3 Track A same-day history semantics

The Yelp dataset exposes dates, not timestamps.

**Resolution:** All Track A user-history and business-history features must use data from **strictly earlier dates only**. Same-day ordering is not allowed. The accepted implementation pattern is:

- aggregate to user-day and business-day
- lag by one full day
- attach the same prior-history values to all reviews on that date

Any logic that orders same-day reviews by `review_id`, or otherwise fabricates intra-day order, is invalid.

### 2.4 Track A first-review bucketing

**Resolution:** first-review rows are identified by `user_prior_review_count = 0`.

The first bucket label is:

- `0 (first review)`

This must not rely on `IS NULL`.

### 2.5 Track B snapshot framing

Track B is a single-snapshot usefulness ranking task.

**Resolution:** Track B must not claim the dataset supports vote-growth reconstruction, future usefulness prediction, or any other temporal target that exceeds a single-snapshot interpretation.

### 2.6 Track B pairwise feasibility math

**Resolution:** pairwise feasibility must be based on **non-tied** pairs, not raw combinations.

The required calculation is:

`valid_pairs = C(n, 2) - tied_pairs`

Track B outputs must report both:

- raw pair count: `C(n, 2)`
- net valid pair count: `C(n, 2) - tied_pairs`

Feasibility sign-off must be based on the net valid pair count.

**Tied-pair definition:** a tied pair is two reviews within the same ranking group that have identical raw `useful` vote counts. This is a pre-label definition — ties are computed on the raw `useful` field, not on any constructed label scheme. This matters because zero-inflated `useful` distributions produce a large number of 0-0 ties that would inflate raw pair counts.

### 2.7 Track B leakage / scope validation

Stage 7 for Track B must be a real validation stage rather than a checklist.

**Resolution:** the validation stage must, at minimum:

- check generated label tables for banned simultaneous-observation columns such as `funny` and `cool` — zero tolerance: any occurrence is a Stage 7 failure
- verify labels do not compare reviews across different age buckets
- scan generated markdown and log artifacts for unsupported temporal claims — zero tolerance: any match is a Stage 7 failure
- verify no row-level raw review text is emitted in Track B artifacts

**Temporal claim scan specification:**

Target files: all files matching `outputs/tables/track_b_*` and `outputs/logs/track_b_*`.

Minimum prohibited patterns (case-insensitive regex):

```
predict\s+future
vote\s+growth
future\s+useful(ness)?
temporal\s+target
vote.*(trajectory|trend|accumulate)
usefulness.at.time
reconstruct.*(vote|useful)
```

Implementation: Python `re.search()` with `re.IGNORECASE` over the text content of each target file. Any match produces a named finding in the Stage 7 log and causes Stage 7 to fail. Teams may extend this list but must not reduce it.

### 2.8 Photo scope

Photo data exists locally in a separate raw archive:

- `Dataset(Raw)/Yelp Photos/yelp_photos.tar`

**Resolution:** Photo ingestion is **out of scope** for Tracks A and B and is removed from the shared A/B ingestion contract. If a future track needs photo data, it must add a separate ingestion path rather than extending the Track A/B shared pipeline implicitly.

### 2.9 Row-loss policy for `review_fact`

Shared joins may drop rows only under a tightly bounded, explicit gate.

**Resolution:** set:

- `quality.review_fact_max_row_loss_fraction: 0.001`

That is a maximum allowable drop fraction of **0.1%**.

Enforcement:

- if `dropped_rows / raw_review_count > 0.001`, fail the shared pipeline
- if row loss is non-zero but `<= 0.001`, continue only after logging orphan `review_id` values and the missing foreign-key reason

This is the approved policy for implementation.

### 2.10 Stage 8 artifact paths

The completion artifact for both tracks is markdown under `outputs/tables/`.

**Resolution:**

- Track A summary path: `outputs/tables/track_a_s8_eda_summary.md`
- Track B summary path: `outputs/tables/track_b_s8_eda_summary.md`

Any alternate Stage 8 summary location is non-compliant.

### 2.11 Snapshot metadata contract

Track B requires a materialized snapshot manifest rather than re-inferring the snapshot date inside each stage.

**Resolution:** `data/curated/snapshot_metadata.json` must include:

```json
{
  "snapshot_reference_date": "2022-01-19",
  "dataset_release_tag": "yelp_academic_2022",
  "computed_from": "MAX(review_date, tip_date)"
}
```

Required fields:

- `snapshot_reference_date`
- `dataset_release_tag`

Optional provenance field:

- `computed_from`

Track B stages must read this file and must not independently re-infer the snapshot date.

---

## 3. Subagent Ownership and Prompt Precedence

### 3.1 Shared-code ownership

The main agent owns all shared ingestion, validation, curation, configuration, and dependency files for Tracks A and B.

Main-agent-owned areas:

- `src/common/*`
- `src/ingest/*`
- `src/validate/*`
- `src/curate/*`
- `configs/*`
- `requirements.txt`

### 3.2 Track-specific ownership

Track A subagent may create or modify only:

- `src/eda/track_a/*`
- `outputs/tables/track_a_*`
- `outputs/figures/track_a_*`
- `outputs/logs/track_a_*`

Track B subagent may create or modify only:

- `src/eda/track_b/*`
- `outputs/tables/track_b_*`
- `outputs/figures/track_b_*`
- `outputs/logs/track_b_*`

**Data access constraint:** ownership rules apply to both Parquet files and DuckDB views/tables with the same logical name. Track A must not query the DuckDB view `review_fact_track_b` or read the file `review_fact_track_b.parquet`. This constraint covers all access paths — file reads, DuckDB queries, and programmatic joins.

### 3.3 Prompt conflict handling

Some existing agent docs still assign shared ingestion and curation work to Track A or use outdated input names for Track B.

**Resolution:** until the source docs are synced, any launch prompt for Track A / Track B subagents must explicitly override conflicting legacy text and restate:

- shared pipeline code is main-agent-owned
- Track A reads `review_fact.parquet`
- Track B reads `review_fact_track_b.parquet`
- Track A must not use snapshot-only fields
- Track B must read `snapshot_metadata.json`

This override is temporary. The long-term fix is doc sync, not prompt drift.

**Expiry rule:** once all documents in Section 4 are synced and Section 5 item 7 (source-doc sync completeness verification) passes, prompt overrides must be removed from launch prompts. Implementation agents must not launch with prompt overrides after sync is confirmed — all contract details must come from the synced documents themselves.

---

## 4. Required Source-Doc Sync Before Execution

The following documents must be updated to match this memo before implementation begins:

1. `07_Implementation_Plan_Ingestion_TrackA_TrackB.md`
   - ensure all A/B contracts, Stage 8 paths, snapshot metadata schema, row-loss gate, and validation requirements match this memo

2. `track_a/AGENTS.md`
   - remove shared ingestion / curation ownership from the Track A agent (currently lines 15-16 assign ingestion and curation to Track A)
   - keep Track A focused on `src/eda/track_a/*`

3. `track_a/CLAUDE.md`
   - add explicit statement that Track A reads `review_fact.parquet` exclusively
   - add the banned-field list from Section 2.2
   - add the direct-join constraint from Section 2.2

4. `track_a/02_EDA_Pipeline_Track_A_Future_Ratings.md`
   - reconcile `review_fact` column definitions with the implementation SQL in document 07 — the pipeline spec's column list must match the actual `review_fact.parquet` schema produced by `build_review_fact.py`

5. `track_b/03_EDA_Pipeline_Track_B_Usefulness_Ranking.md`
   - update Track B input references from `review_fact.parquet` to `review_fact_track_b.parquet`
   - align the snapshot metadata contract

6. `track_b/AGENTS.md`
   - add explicit reference to `review_fact_track_b.parquet` as the Track B input
   - add requirement to read `snapshot_metadata.json` for the snapshot reference date
   - add Stage 7 validation expectations including the prohibited temporal claim patterns

7. `track_b/CLAUDE.md`
   - add explicit statement that Track B reads `review_fact_track_b.parquet`
   - add requirement to read `snapshot_metadata.json`
   - add reference to Stage 7 validation expectations

If any synced document conflicts with this memo, the sync is incomplete and implementation remains blocked.

---

## 5. Verification Expectations

Resolution of the planning issues is not complete unless the verification logic independently checks the highest-risk failure modes.

Required verification after implementation:

1. **Track A banned-field verification**
   - confirm Track A artifacts and feature inputs do not reintroduce banned snapshot-only or lifetime aggregate fields
   - confirm Track A code paths do not read from `review_fact_track_b.parquet` or the DuckDB view `review_fact_track_b` at runtime
   - confirm any raw entity file reads (e.g., `review.parquet` for text) do not join or extract banned fields

2. **Track A as-of verification**
   - confirm prior-history logic uses earlier dates only
   - confirm no same-day ordering surrogate is used

3. **Track B pairwise verification**
   - confirm Stage 6 reports both raw and net valid pair counts
   - confirm net valid pairs subtract tied pairs correctly
   - confirm tied pairs are computed on raw `useful` counts, not constructed labels

4. **Track B scope verification**
   - confirm `funny` and `cool` are absent from generated candidate feature tables
   - confirm no cross-age label comparison is present
   - confirm no unsupported temporal claims appear in markdown or logs (per the prohibited regex patterns in Section 2.7)
   - confirm no row-level raw review text appears in output artifacts

5. **Shared pipeline verification**
   - confirm `review_fact.parquet`, `review_fact_track_b.parquet`, and `snapshot_metadata.json` are all materialized
   - confirm row-loss handling follows the 0.1% gate exactly
   - confirm `snapshot_metadata.json` value-level correctness: assert `snapshot_reference_date` equals `MAX(review_date)` computed from the actual ingested data, not a hardcoded placeholder
   - confirm orphan log (when row loss is non-zero but within threshold) contains actual `review_id` values and the missing foreign-key reason for each

6. **Completion artifact verification**
   - confirm Stage 8 markdown files exist at:
     - `outputs/tables/track_a_s8_eda_summary.md`
     - `outputs/tables/track_b_s8_eda_summary.md`

7. **Source-doc sync completeness verification** (pre-launch gate)
   - confirm all documents listed in Section 4 have been updated
   - confirm no listed document conflicts with this memo
   - this verification must pass before any Track A or Track B subagent is launched

Subagent self-reporting is not sufficient by itself for these checks.

---

## 6. Closure of Adversarial Findings

This memo resolves the seven findings from the PM adversarial review as follows:

| Finding | Resolution |
|---|---|
| #1 Snapshot fields leak into Track A | Split curated outputs into `review_fact` and `review_fact_track_b`; ban snapshot-only fields from Track A |
| #2 Same-day ordering conflict | Require strictly earlier-date semantics via day-level aggregation and lag |
| #3 Photo path mismatch | Remove photo from the Track A/B shared ingestion contract |
| #4 Pairwise math overstates feasibility | Require `valid_pairs = C(n,2) - tied_pairs` and report both raw and net counts |
| #5 Track B leakage is checklist-only | Require real automated validation of columns, age isolation, claims, and text leakage |
| #6 First-review bucket bug | Require `user_prior_review_count = 0` for first-review bucket |
| #7 Silent row loss | Set hard gate at `review_fact_max_row_loss_fraction = 0.001` with orphan logging below threshold |

---

## 7. Bottom Line

The Track A / Track B plan is approved only in the form resolved by this memo.

The project may proceed to implementation **after** the listed source documents are synced to these decisions. Until then, this memo serves as the decision record, but not yet as permission to launch execution agents against unsynced planning documents.
