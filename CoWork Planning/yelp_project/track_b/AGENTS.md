# Track B — Agent Configuration: Usefulness Ranking

## Agent Purpose

This agent implements the EDA pipeline for **Track B: building a snapshot, age-controlled ranking setup for comparatively useful reviews**. It is a data profiling and label engineering agent — it does not train ranking models.

## Context

You are working on a semester-scale data science project using the **Yelp Open Dataset**. Track B asks: *At a fixed dataset snapshot, can you rank comparatively useful reviews within a business/category after controlling for review age?*

Your job is to execute the EDA pipeline defined in `03_EDA_Pipeline_Track_B_Usefulness_Ranking.md`. Read that file first.

## Agent Responsibilities

1. **Read** `data/curated/review_fact_track_b.parquet` as the Track B curated input and read `data/curated/snapshot_metadata.json` for the materialized snapshot reference date.
2. **Profile** the distribution of `useful` votes and review ages — expect severe zero-inflation and a long tail.
3. **Quantify** age confounding and define age buckets for valid comparison.
4. **Define ranking groups** — business-first with category fallback — and assess group sizes for LTR feasibility.
5. **Construct candidate snapshot-safe label schemes** (binary, graded, within-group percentile, top-decile).
6. **Assess feasibility** for pointwise, pairwise, and listwise learning inside age-controlled groups, reporting both raw pair counts and net valid non-tied pair counts.
7. **Run Stage 7 validation** as a real enforcement stage: ban `funny`/`cool`, block cross-age comparisons, scan Track B markdown/log artifacts for unsupported temporal claims, and confirm no row-level raw review text is emitted.

## Key Constraints

- Track B reads `data/curated/review_fact_track_b.parquet`. Do not fall back to `review_fact.parquet` when older docs mention it.
- Track B must read `data/curated/snapshot_metadata.json` and must not independently re-infer the snapshot date inside each stage.
- The `useful` field is the target signal. `funny` and `cool` are banned simultaneous-observation columns; their presence in generated label tables is a Stage 7 failure.
- This is a single-snapshot task. Do not claim the dataset supports vote trajectories or usefulness-at-time reconstruction.
- Exposure-time bias is the dominant confounder: older reviews have had more time to collect votes.
- Ranking groups must be age-controlled.
- Stage 6 pairwise feasibility is based on non-tied pairs: `valid_pairs = C(n, 2) - tied_pairs`, where ties are defined on raw `useful` values within a ranking group.
- Outputs are aggregate-only. No raw review text in figures or tables.
- CLI-first: all stages are `python -m src.eda.track_b.<stage> --config configs/track_b.yaml`.
- Stage 8 completes only when `outputs/tables/track_b_s8_eda_summary.md` exists.

## Data Entities Needed

- `review` — core table (useful votes, text, stars, date)
- `business` — categories, city
- `user` — elite status, fans
- `snapshot_metadata` — manifest with `snapshot_reference_date`, `dataset_release_tag`, and optional `computed_from`

## Completion Signal

EDA is done when `outputs/tables/track_b_s8_eda_summary.md` exists and all exit criteria are met.
