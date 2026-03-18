# Workflow: Running the Track B Pipeline

This document provides a step-by-step guide for running the **Track B** pipeline (Snapshot Usefulness Ranking).

## Prerequisites

1.  **Environment**: Ensure you have Python 3.8+ installed and dependencies are loaded:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Shared Foundation**: The Track B pipeline requires the shared curation layer and snapshot metadata.
    ```bash
    python scripts/run_pipeline.py --approach shared
    ```
    *Verify `data/curated/review_fact_track_b.parquet` and `data/curated/snapshot_metadata.json` exist.*

## Standard Execution

Run the full Track B pipeline via the launcher:

```bash
python scripts/run_pipeline.py --approach track_b
```

### Manual Execution (Stage by Stage)

| Stage | Command |
| :--- | :--- |
| **S1: Vote Distribution** | `python -m src.eda.track_b.usefulness_distribution --config configs/track_b.yaml` |
| **S2: Age Confounding** | `python -m src.eda.track_b.age_confounding --config configs/track_b.yaml` |
| **S3: Ranking Groups** | `python -m src.eda.track_b.ranking_group_analysis --config configs/track_b.yaml` |
| **S4: Label Construction** | `python -m src.eda.track_b.label_construction --config configs/track_b.yaml` |
| **S5: Feature Correlates** | `python -m src.eda.track_b.feature_correlates --config configs/track_b.yaml` |
| **S6: Feasibility Check** | `python -m src.eda.track_b.training_feasibility --config configs/track_b.yaml` |
| **S7: Leakage/Scope Check** | `python -m src.eda.track_b.leakage_scope_check --config configs/track_b.yaml` |
| **S8: Summary Report** | `python -m src.eda.track_b.summary_report --config configs/track_b.yaml` |

## Monitoring Outputs

*   **Tables**: `outputs/tables/track_b_*`
*   **Figures**: `outputs/figures/track_b_*`
*   **Logs**: `outputs/logs/track_b_*`

## Key Constraints Reference

*   **Target**: `useful` votes.
*   **Banned**: `funny`, `cool` (simultaneous-observation leakage).
*   **Grouping**: Always compare within **age buckets** defined in `configs/track_b.yaml`.
*   **Snapshot**: All logic must reference the `snapshot_reference_date` in `data/curated/snapshot_metadata.json`.

---
*Last Updated: 2026-03-12*
