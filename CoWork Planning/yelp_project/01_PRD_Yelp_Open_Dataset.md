# Product Requirements Document: Yelp Open Dataset — Semester-Scale Data Science Project

**Version:** 1.0
**Date:** 2026-03-10
**Status:** Draft
**Authors:** Brooklyn (Project Lead)

---

## 1. Background and Motivation

Star ratings are the currency of online reputation, yet the mechanisms behind how ratings form, what makes a review useful, and whether recommendation surfaces are equitable remain poorly understood at scale. The Yelp Open Dataset offers a rare, multi-entity relational dataset spanning businesses, users, reviews, tips, check-ins, and photos — large enough and rich enough to support rigorous, semester-scale investigation across prediction, ranking, temporal analysis, recommendation, and fairness.

This project treats the Yelp Open Dataset not as a homework exercise but as a **production-grade data science engagement**: engineered pipelines, strict temporal evaluation, governance-aware outputs, and modular architecture suitable for team collaboration.

---

## 2. Dataset Fit and Rationale

The Yelp Open Dataset is distributed as line-delimited JSON files covering six core entities:

| Entity | Description | Key Fields |
|---|---|---|
| **business** | Business metadata, location, categories, attributes | `business_id`, `name`, `city`, `state`, `categories`, `attributes`, `stars`, `review_count` |
| **review** | Full review text with star rating and votes | `review_id`, `user_id`, `business_id`, `stars`, `date`, `text`, `useful`, `funny`, `cool` |
| **user** | User profile with history aggregates and social graph | `user_id`, `name`, `review_count`, `yelping_since`, `friends`, `elite`, `fans`, `average_stars` |
| **tip** | Short tips from users about businesses | `user_id`, `business_id`, `text`, `date`, `compliment_count` |
| **checkin** | Aggregated check-in timestamps per business | `business_id`, `date` |
| **photo** | Photo metadata linked to businesses | `photo_id`, `business_id`, `caption`, `label` |

**Why this dataset fits a semester project:**

- Multi-entity relational structure forces real data engineering decisions (joins, fan-out, sparsity).
- Temporal dimension enables strict train/validation/test chronological splits.
- Text, numeric, categorical, and graph features coexist, requiring cross-modal integration.
- Scale is large enough to require thoughtful compute/storage choices but manageable on a single machine or small cluster.
- Rich enough to support five distinct research tracks under one unified data backbone.

---

## 3. Product Vision

Deliver a **reproducible, CLI-driven analytical platform** for a **closed academic project** that answers five interconnected research questions about Yelp's ecosystem. The platform should produce private, aggregate-safe analytical artifacts, curated feature tables, and evaluation reports for team/instructor use only — not a public product, public dashboard, or portfolio demo.

---

## 4. Core Research Questions

| Track | Question |
|---|---|
| **A** | How well can review text, user history, and business attributes predict future star ratings under strict time-split evaluation? |
| **B** | At a fixed dataset snapshot, can you rank comparatively useful reviews within a business/category after controlling for review age? |
| **C** | How does sentiment and topic prevalence shift over time across cities/neighborhoods, and what events or business changes correlate with those shifts? |
| **D** | Can separate business-cold-start and user-cold-start recommenders outperform explicit as-of popularity baselines? |
| **E** | What patterns of bias or disparity appear in ratings and recommendations across neighborhoods or business categories, and how can models be constrained or corrected? |

---

## 5. Users and Stakeholders

| Role | Interest |
|---|---|
| **Project team** | Execute semester project; build presentation-quality academic work |
| **Course instructor / advisor** | Evaluate rigor, reproducibility, and analytical depth |
| **Peer reviewers** | Understand methodology; reproduce results |
| **Future maintainers** | Extend or adapt pipelines for new questions |

---

## 6. Scope

### In Scope

- Ingestion, validation, and curation of all six Yelp entity files into a local analytical warehouse (Parquet-based).
- Exploratory data analysis pipelines for all five tracks, structured as CLI-executable stages.
- Feature engineering tables with strict temporal ("as-of") construction.
- Baseline models and evaluation harnesses for each track.
- Aggregate-safe internal reporting: course presentation artifacts, summary tables, notebook exports, and visualizations that never display raw review text in shared outputs.
- Documentation: this PRD, per-track EDA specs, and a final report.

### Non-Goals (Out of Scope)

- Real-time serving infrastructure or API deployment.
- Photo/image modeling (photos may be used as metadata features but deep vision pipelines are excluded).
- Social graph analysis beyond user-level friend count or elite status as features.
- Replication of Yelp's proprietary ranking algorithms.
- Any public redistribution of raw data, row-level derived data, or presentation artifacts outside the academic team/instructor context.

---

## 7. Data Assets and Entity Map

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ business │◄────│  review  │────►│   user   │
│          │     │          │     │          │
│ id       │     │ id       │     │ id       │
│ city     │     │ stars    │     │ since    │
│ state    │     │ date     │     │ friends  │
│ categories│    │ text     │     │ elite    │
│ attributes│    │ useful   │     │ avg_stars│
│ stars    │     │ funny    │     │ fans     │
│ review_ct│     │ cool     │     │          │
└────┬─────┘     └──────────┘     └──────────┘
     │
     ├──► tip (user_id, business_id, date, text)
     ├──► checkin (business_id, date)
     └──► photo (business_id, label, caption)
```

**Key relational considerations:**

- Reviews are the central fact table; business and user are dimension tables.
- Tips and check-ins provide supplementary temporal signals.
- The user `friends` field encodes a social graph (comma-separated user IDs) — useful as a feature source but not a modeling target in this project.
- All temporal joins must respect "as-of" semantics: features for a prediction at time *t* may only use data strictly before *t*.

---

## 8. Functional Requirements

### 8.1 Ingestion

| ID | Requirement |
|---|---|
| F-01 | Ingest all six Yelp JSON files into Parquet format with schema validation. |
| F-02 | Preserve original field types; cast dates to proper datetime. |
| F-03 | Log row counts, null rates, and schema mismatches per entity. |

### 8.2 Curation

| ID | Requirement |
|---|---|
| F-04 | Build a `review_fact` table joining review, business, and user metadata with temporal keys. |
| F-05 | Build per-track curated tables as specified in each track's EDA pipeline doc. |
| F-06 | All derived tables must record their lineage (source tables, filter criteria, date range). |

### 8.3 EDA

| ID | Requirement |
|---|---|
| F-07 | Each track has a dedicated EDA pipeline producing summary tables, figures, and validation logs. |
| F-08 | EDA pipelines are CLI-executable and config-driven. |
| F-09 | EDA outputs are written to `outputs/tables/` and `outputs/figures/` with consistent naming. |

### 8.4 Evaluation Harness

| ID | Requirement |
|---|---|
| F-10 | Temporal split definitions are centralized for predictive tracks; any exceptions must be explicitly documented. |
| F-11 | Track A uses MAE/RMSE on held-out future reviews. |
| F-12 | Track B uses snapshot-time, age-controlled ranking evaluation (e.g., NDCG@K) within documented review groups. |
| F-13 | Track C reports trend stability and event-correlation metrics. |
| F-14 | Track D evaluates business-cold-start and user-cold-start cohorts separately against explicit as-of popularity baselines. |
| F-15 | Track E reports disparity metrics (e.g., demographic parity, calibration gap) at aggregate level. |

---

## 9. Analytical Requirements

- Tracks A and D must use **strict chronological splits**: train on data before cutoff *T₁*, validate on *T₁ – T₂*, test on data after *T₂*.
- Track B is a **single-snapshot ranking task** and must document its age-control strategy, grouping logic, and any split exception explicitly.
- Feature construction must be **as-of**: a feature for a review at time *t* uses only data available before *t*.
- Text features should be summarized as aggregate statistics or embeddings, never raw text in outputs.
- All geographic analyses should use **city and neighborhood aggregation**, never individual-business-level public display.
- **Leakage audits** are mandatory before any modeling begins.
- Mutable business metadata (e.g., categories, hours, attributes) must be treated as snapshot fields unless an as-of reconstruction is available; predictive tracks should restrict them to clearly documented, low-risk uses.

---

## 10. Governance, Licensing, and Privacy Constraints

| Constraint | Implication |
|---|---|
| Yelp Dataset Terms of Use | No redistribution of raw data; outputs must be derivative, not copies. |
| Academic-use boundary | All deliverables are for closed academic/team/instructor use only; no public portfolio, public dashboard, or public redistribution. |
| Review text privacy | Shared artifacts must use aggregate summaries, topic distributions, or derived features only — never verbatim review text or snippets. |
| User identity | User IDs are pseudonymous but should not be linked to real identities. |
| Demographic inference | Do not infer protected demographic attributes from usernames or review text. |
| Row-level artifacts | Raw tables and row-level derived tables remain internal workspace artifacts and are not exported outside the team/instructor context. |
| Output publication | Any shared report, notebook, or presentation should present **aggregate-only** metrics. |

---

## 11. Success Metrics

| Track | Primary Metric | Target |
|---|---|---|
| A | MAE on future star prediction (test set) | Measurably below naïve mean/median baseline |
| B | NDCG@10 for age-controlled snapshot usefulness ranking | Measurably above age-only and length-only baselines |
| C | Interpretability of detected trends | Trends validated against known events or business changes |
| D | Recall@20 / NDCG@10 for D1 and D2 separately | Each subtrack above its as-of popularity baseline |
| E | Documented disparity metrics | Quantified gaps with at least one proposed mitigation lever |

**Project-level success criteria:**

- All five EDA pipelines execute end-to-end from raw JSON to output artifacts via CLI.
- Temporal splits and documented evaluation exceptions are consistent and auditable across tracks.
- Final report is reproducible from the repo with documented commands.
- No governance violations in any shared academic artifact.

---

## 12. Evaluation Plan

### 12.1 Temporal Split Strategy

```
|<---- TRAIN ---->|<-- VAL -->|<-- TEST -->|
                  T₁          T₂
```

- **T₁** and **T₂** are selected during EDA based on review volume distribution.
- Recommended starting point: T₁ at the 70th percentile of review dates, T₂ at the 85th percentile.
- Exact cutoffs are finalized after temporal profiling in Track A's EDA.

### 12.2 Evaluation Taxonomy

| Type | Metrics | Tracks |
|---|---|---|
| Regression | MAE, RMSE, calibration plots | A |
| Ranking | NDCG@K, Recall@K, MAP | B, D |
| Trend analysis | Slope significance, changepoint detection | C |
| Fairness | Demographic parity, equalized odds, calibration gap | E |

---

## 13. Delivery Roadmap

| Week | Milestone | Deliverables |
|---|---|---|
| 1–2 | **Ingestion & Validation** | Parquet warehouse, schema reports, row-count logs |
| 3–4 | **Curation & Shared Features** | `review_fact`, temporal split table, user/business dimension tables |
| 5–7 | **Track EDA Pipelines** | Per-track EDA outputs (tables, figures, validation logs) |
| 8–10 | **Baseline Modeling** | Per-track baseline models, evaluation reports |
| 11–12 | **Iteration & Advanced Models** | Improved models, ablation studies |
| 13–14 | **Reporting & Governance Review** | Final report, dashboard, governance audit |
| 15 | **Presentation & Handoff** | Slide deck, repo cleanup, reproducibility check |

---

## 14. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Temporal leakage in features | High | Critical | Mandatory as-of construction; leakage audit pipeline stage |
| Sparse user/business histories | Medium | High | Explicit cold-start cohort handling (Track D); sparsity reports |
| Imbalanced usefulness votes | High | Medium | Label engineering in Track B; zero-inflation analysis |
| Geographic coverage gaps | Medium | Medium | Coverage profiling in Track C & E; scope to well-covered cities |
| Compute constraints on text processing | Medium | Medium | Batch processing; pre-computed embeddings; sampling for EDA |
| Governance violation in outputs | Low | Critical | Internal-academic-only policy; aggregate-only shared artifacts; no row-level exports |
| Invalid Track B target design | High | High | Treat Track B as a snapshot ranking task with age controls; do not infer vote trajectories |

---

## 15. Deliverables

| # | Artifact | Format |
|---|---|---|
| 1 | This PRD | Markdown |
| 2 | EDA pipeline spec per track (×5) | Markdown |
| 3 | Ingested Parquet warehouse | `data/raw/`, `data/curated/` |
| 4 | EDA output tables and figures | `outputs/tables/`, `outputs/figures/` |
| 5 | Baseline model evaluation reports | Markdown + CSV |
| 6 | Final project report | Markdown or PDF |
| 7 | Internal academic dashboard / notebook export | HTML or notebook export (course/team only) |
| 8 | Reproducibility guide | README.md |

---

## 16. Recommended Repository Layout

```
yelp-semester-project/
├── README.md
├── configs/
│   ├── base.yaml              # Shared paths, split dates, random seeds
│   ├── track_a.yaml
│   ├── track_b.yaml
│   ├── track_c.yaml
│   ├── track_d.yaml
│   └── track_e.yaml
├── data/
│   ├── raw/                   # Original Yelp JSON (gitignored)
│   ├── interim/               # Intermediate processing artifacts
│   ├── curated/               # Final analytical tables (Parquet)
│   └── reports/               # Data quality and profiling reports
├── src/
│   ├── __init__.py
│   ├── ingest/
│   │   ├── load_yelp_json.py
│   │   └── raw_to_parquet.py
│   ├── validate/
│   │   ├── schema_checks.py
│   │   └── leakage_audit.py
│   ├── curate/
│   │   ├── build_review_fact.py
│   │   ├── build_user_dim.py
│   │   └── build_business_dim.py
│   ├── features/
│   │   ├── temporal_features.py
│   │   ├── text_features.py
│   │   └── user_history.py
│   └── eda/
│       ├── track_a/
│       │   ├── temporal_profile.py
│       │   └── ...
│       ├── track_b/
│       │   ├── usefulness_distribution.py
│       │   └── ...
│       ├── track_c/
│       │   ├── geo_coverage.py
│       │   └── ...
│       ├── track_d/
│       │   ├── business_cold_start.py
│       │   ├── user_cold_start.py
│       │   └── ...
│       └── track_e/
│           ├── subgroup_definition.py
│           └── ...
├── outputs/
│   ├── figures/
│   ├── tables/
│   └── logs/
├── tests/
│   └── ...
├── docs/
│   ├── 01_PRD_Yelp_Open_Dataset.md
│   ├── track_a/
│   │   ├── 02_EDA_Pipeline_Track_A_Future_Ratings.md
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md
│   ├── track_b/
│   │   ├── 03_EDA_Pipeline_Track_B_Usefulness_Ranking.md
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md
│   ├── track_c/
│   │   ├── 04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md
│   ├── track_d/
│   │   ├── 05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md
│   └── track_e/
│       ├── 06_EDA_Pipeline_Track_E_Bias_Disparity.md
│       ├── AGENTS.md
│       └── CLAUDE.md
└── requirements.txt
```

---

## 17. Shared Conventions

### CLI Pattern

All pipeline stages follow a consistent invocation pattern:

```bash
python -m src.<module>.<script> --config configs/<config>.yaml
```

### Config Structure (base.yaml example)

```yaml
paths:
  raw: data/raw
  interim: data/interim
  curated: data/curated
  outputs: outputs

splits:
  train_end: "2019-01-01"      # Placeholder — finalized during EDA
  val_end: "2020-01-01"        # Placeholder — finalized during EDA

random_seed: 42
log_level: INFO
```

### Output Naming Convention

```
outputs/tables/{track}_{stage}_{description}.parquet
outputs/figures/{track}_{stage}_{description}.png
outputs/logs/{track}_{stage}_{timestamp}.log
```

### Governance Checklist (Pre-Publication)

Before any artifact is shared externally:

1. The artifact is for internal academic use only and is not published publicly.
2. No raw review text or verbatim snippets appear in shared figures, tables, notebooks, or slides.
3. No row-level tables, IDs, or near-raw exports are shared outside the team/instructor context.
4. All geographic outputs use city/neighborhood aggregation (minimum group size ≥ 10).
5. No user IDs are linkable to real identities.
6. No demographic attributes have been inferred from names or text.
7. Output file sizes are reasonable (no accidental data dumps).

---

*End of PRD.*
