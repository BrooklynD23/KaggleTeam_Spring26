# KaggleTeam Spring 2026

Yelp Open Dataset semester project for the CPP DS and AI Spring 2026 team. The repository combines planning documents, a shared ingestion and curation pipeline, and implemented EDA workflows for Tracks A, B, C, D, and E.

## Repository Status

Last documentation refresh: 2026-03-19.

Current repo state:

- Shared ingestion, schema validation, curated table building, and orchestration code are implemented.
- Track A, Track B, Track C, Track D, and Track E EDA pipelines are implemented in `src/eda/track_a/`, `src/eda/track_b/`, `src/eda/track_c/`, `src/eda/track_d/`, and `src/eda/track_e/`.
- Track D Stage 7 (evaluation cohorts) uses bounded, deterministic construction with `evaluation.entity_cap_per_group` to stay tractable on the Yelp dataset.
- `data/raw/`, `data/curated/`, and `outputs/` are present (curated and outputs may be populated after pipeline runs).
- Tests exist for key contract and regression checks, especially around leakage rules and Track B feasibility logic.

## Project Structure

```text
.
|- configs/                    Shared and track-specific YAML configuration
|- data/
|  |- raw/                     Extracted Yelp JSON files after ingestion setup
|  |- interim/                 Optional intermediate assets
|  |- curated/                 Shared curated parquet artifacts
|- outputs/
|  |- figures/                 Generated charts per stage
|  |- logs/                    Pipeline and validation logs
|  |- tables/                  Parquet and markdown deliverables
|- scripts/                    Entry points and pipeline dispatcher
|- src/
|  |- ingest/                  JSON extraction and database loading
|  |- validate/                Schema and contract checks
|  |- curate/                  Shared curated table construction
|  |- eda/track_a/             Implemented Track A EDA stages
|  |- eda/track_b/             Implemented Track B EDA stages
|  |- eda/track_c/             Implemented Track C EDA stages
|  |- eda/track_d/             Implemented Track D cold-start EDA stages
|  |- eda/track_e/             Implemented Track E bias/disparity EDA stages
|- tests/                      Regression and contract tests
|- notebooks/                  Jupyter EDA on stratified sample (see Notebook EDA below)
|- CoWork Planning/
|  |- Dataset(Raw)/            Local raw archives and reference assets
|  |- yelp_project/            PRD, implementation plans, and per-track planning docs
```

## Data Context Before Processing

This project is built around the Yelp Open Dataset. Before any pipeline runs, the repo expects:

- Raw Yelp archives to exist locally under `CoWork Planning/Dataset(Raw)/`.
- The main review/business/user/tip/checkin archive at `CoWork Planning/Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar`.
- Optional photo data at `CoWork Planning/Dataset(Raw)/Yelp Photos/yelp_photos.tar`.

Shared data flow:

1. Raw tar archive in `CoWork Planning/Dataset(Raw)/...`
2. Extract NDJSON files into `data/raw/`
3. Load entities into DuckDB at `data/yelp.duckdb`
4. Materialize curated parquet outputs into `data/curated/`
5. Run per-track EDA stages and write artifacts to `outputs/tables/`, `outputs/figures/`, and `outputs/logs/`

Important constraints from the current plan:

- Track A and Track B depend on the shared curated layer first.
- Photo data is currently out of scope for the shared Track A and Track B ingestion contract.
- No raw review text should appear in shared academic deliverables.
- Track A must obey strict as-of feature construction.
- Track B is framed as a snapshot ranking task, not future vote-growth prediction.

## Progress Tracking

The table below reflects the state of the repo against the planning documents currently checked in.

| Area | Planned in docs | Code status | Output status | Notes |
| --- | --- | --- | --- | --- |
| Shared ingestion and curation | Yes | Implemented | Not materialized in repo | `src/ingest/`, `src/validate/`, `src/curate/`, dispatcher, configs |
| Track A: Future Star Rating Prediction | Yes | Implemented | Not materialized in repo | 8 EDA stage modules present; summary/report path defined |
| Track B: Snapshot Usefulness Ranking | Yes | Implemented | Not materialized in repo | 8 EDA stage modules present; feasibility and leakage checks covered by tests |
| Track C: Sentiment and Topic Drift | Yes | Implemented | Materialized when run | EDA stages in `src/eda/track_c/` |
| Track D: Cold-Start Recommender | Yes | Implemented | Materialized when run | 9 EDA stages; Stage 7 uses bounded construction with `entity_cap_per_group` |
| Track E: Bias and Disparity | Yes | Implemented | Materialized when run | 9 EDA stages in `src/eda/track_e/` |

## Track Folder Check

Per-track folders already exist in the planning workspace:

- `CoWork Planning/yelp_project/track_a/`
- `CoWork Planning/yelp_project/track_b/`
- `CoWork Planning/yelp_project/track_c/`
- `CoWork Planning/yelp_project/track_d/`
- `CoWork Planning/yelp_project/track_e/`

Those folders now serve as the documentation homes for each track and include a track README plus the existing pipeline spec, `AGENTS.md`, and `CLAUDE.md` files.

Implementation folders under `src/eda/` exist for:

- `track_a`
- `track_b`
- `track_c`
- `track_d`
- `track_e`

## Track Index

| Track | Research focus | Planning folder | Track README |
| --- | --- | --- | --- |
| A | Future star rating prediction under strict temporal splits | `CoWork Planning/yelp_project/track_a/` | [Track A README](CoWork%20Planning/yelp_project/track_a/README.md) |
| B | Snapshot usefulness ranking with age-controlled groups | `CoWork Planning/yelp_project/track_b/` | [Track B README](CoWork%20Planning/yelp_project/track_b/README.md) |
| C | Sentiment and topic drift over time and geography | `CoWork Planning/yelp_project/track_c/` | [Track C README](CoWork%20Planning/yelp_project/track_c/README.md) |
| D | Cold-start recommendation for businesses and users | `CoWork Planning/yelp_project/track_d/` | [Track D README](CoWork%20Planning/yelp_project/track_d/README.md) |
| E | Bias and disparity auditing across groups | `CoWork Planning/yelp_project/track_e/` | [Track E README](CoWork%20Planning/yelp_project/track_e/README.md) |

## Deliverables

Current intended deliverables by layer:

### Shared Deliverables

- `data/yelp.duckdb`
- `data/curated/review_fact.parquet`
- `data/curated/review_fact_track_b.parquet`
- `data/curated/review.parquet`
- `data/curated/business.parquet`
- `data/curated/snapshot_metadata.json`
- Schema validation and orchestration logs under `outputs/logs/`

### Track A Deliverables

- Stage outputs in `outputs/tables/track_a_*`
- Stage figures in `outputs/figures/track_a_*`
- Leakage audit log in `outputs/logs/track_a_*`
- Final EDA summary at `outputs/tables/track_a_s8_eda_summary.md`

### Track B Deliverables

- Stage outputs in `outputs/tables/track_b_*`
- Stage figures in `outputs/figures/track_b_*`
- Leakage and scope validation log in `outputs/logs/track_b_*`
- Final EDA summary at `outputs/tables/track_b_s8_eda_summary.md`

### Track D Deliverables

- Stage outputs in `outputs/tables/track_d_*` (including `track_d_s7_eval_cohorts.parquet`, `track_d_s7_eval_cohort_summary.parquet`, `track_d_s7_eval_candidate_members.parquet`)
- Stage figures in `outputs/figures/track_d_*`
- Leakage check log in `outputs/logs/track_d_s8_leakage_check.log`
- Final EDA summary at `outputs/tables/track_d_s9_eda_summary.md`

### Planning Deliverables

- Master PRD and implementation plans in `CoWork Planning/yelp_project/`
- Per-track pipeline specifications in each `CoWork Planning/yelp_project/track_*/` folder
- Agent guidance docs for track-specific execution

## How to Run

Install Python dependencies first:

```bash
pip install -r requirements.txt
```

Main entrypoints:

```bash
python scripts/run_pipeline.py --help
python scripts/run_pipeline.py
python scripts/run_pipeline.py --approach shared
python scripts/run_pipeline.py --approach track_a
python scripts/run_pipeline.py --approach track_b
```

OS-specific wrappers are also available:

```bash
./run_pipeline.sh
./run_pipeline.sh shared
```

```powershell
.\run_pipeline.ps1
.\run_pipeline.ps1 track_a
```

Execution-engine fallback:

```bash
python scripts/pipeline_dispatcher.py --approach shared
python scripts/pipeline_dispatcher.py --approach track_a --from-stage split_selection
```

### Notebook EDA

Jupyter notebooks run EDA on a stratified sample (~20K reviews) for quick iteration and peer review:

1. Run shared pipeline, then `python -m src.curate.build_sample --config configs/base.yaml`
2. Run notebooks (Track A first; Track D depends on it)
3. Commit executed notebooks and `data/sample/` — peers can review on light laptops without re-running

See [notebooks/README.md](notebooks/README.md) for details.

### Cross-Platform Runtime Notes

- `scripts/run_pipeline.py` is the canonical launcher for both WSL/Linux and native Windows.
- Each runtime uses its own repo-local virtual environment:
  - WSL uses `.venv-wsl`
  - native Windows uses `.venv-win`
  - non-WSL Linux uses `.venv-linux`
- Do not reuse one virtual environment across Windows and WSL. The launcher will pick the runtime-matched environment automatically.
- One invocation should use one runtime only: WSL shell with WSL Python, or Windows PowerShell with Windows Python.
- `scripts/pipeline_dispatcher.py` is now a pure execution entrypoint and expects `--approach`; use the launcher for interactive selection and environment setup.

README drift check:

```bash
python scripts/check_repo_readme_drift.py --report
python scripts/check_repo_readme_drift.py --check
python scripts/check_repo_readme_drift.py --update
```

Optional pre-commit automation:

```bash
python scripts/enable_git_hooks.py
```

That command points Git at the repo-managed `.githooks/` directory. The
pre-commit hook runs the README drift checker in `--check` mode before each
commit and prefers the repo virtual environment when one exists.

Recommended execution order:

1. Run the shared pipeline.
2. Validate that curated artifacts are written to `data/curated/`.
3. Run Track A (required before Track D, which uses Track A Stage 5 splits).
4. Run Track B and/or Track D.
5. Review outputs under `outputs/tables/`, `outputs/figures/`, and `outputs/logs/`.

## Near-Term Plan

Recommended next milestones based on the current repo state:

1. Materialize the shared curated layer from the local Yelp archive.
2. Run Track A and Track B end to end and check artifact completeness.
3. Sync any remaining planning documents to the latest resolution memo for Track A and Track B.
4. Sync any remaining planning documents to the latest implementation state for Tracks C, D, and E.

## Core Planning Documents

- [Semester planning package](CoWork%20Planning/yelp_project/README.md)
- [Master PRD](CoWork%20Planning/yelp_project/01_PRD_Yelp_Open_Dataset.md)
- [Implementation plan for shared ingestion, Track A, and Track B](CoWork%20Planning/yelp_project/07_Implementation_Plan_Ingestion_TrackA_TrackB.md)
- [Resolution memo for Track A and Track B](CoWork%20Planning/yelp_project/09_Resolution_TrackA_TrackB_Implementation_Plan.md)
