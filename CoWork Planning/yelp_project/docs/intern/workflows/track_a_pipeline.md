# Workflow: Running the Track A Pipeline

This document provides a step-by-step guide for running the **Track A** pipeline (Future Star Rating Prediction).

## Prerequisites

1.  **Environment**: Ensure you have Python 3.8+ installed and dependencies are loaded:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Shared Foundation**: The Track A pipeline requires the shared curation layer to be completed first.
    ```bash
    python scripts/run_pipeline.py --approach shared
    ```
    *Verify `data/curated/review_fact.parquet` exists.*

## Standard Execution

The easiest way to run the full Track A pipeline is via the launcher:

```bash
python scripts/run_pipeline.py --approach track_a
```

### Manual Execution (Stage by Stage)

If you need to run specific stages or debug, you can run the modules directly using `python -m`:

| Stage | Command |
| :--- | :--- |
| **S1: Temporal Profile** | `python -m src.eda.track_a.temporal_profile --config configs/track_a.yaml` |
| **S2: Text Profile** | `python -m src.eda.track_a.text_profile --config configs/track_a.yaml` |
| **S3: User History** | `python -m src.eda.track_a.user_history_profile --config configs/track_a.yaml` |
| **S4: Biz Attributes** | `python -m src.eda.track_a.business_attr_profile --config configs/track_a.yaml` |
| **S5: Split Selection** | `python -m src.eda.track_a.split_selection --config configs/track_a.yaml` |
| **S6: Leakage Audit** | `python -m src.eda.track_a.leakage_audit --config configs/track_a.yaml` |
| **S7: Feature Availability** | `python -m src.eda.track_a.feature_availability --config configs/track_a.yaml` |
| **S8: Summary Report** | `python -m src.eda.track_a.summary_report --config configs/track_a.yaml` |

## Monitoring Outputs

As the pipeline runs, monitor the following directories for artifacts:

*   **Tables**: `outputs/tables/track_a_*` (Parquet and Markdown summaries)
*   **Figures**: `outputs/figures/track_a_*` (Charts and visualizations)
*   **Logs**: `outputs/logs/track_a_*` (Execution logs and Audit reports)

## Common Troubleshooting

*   **Leakage Failures**: If Stage 6 (Leakage Audit) fails, check `outputs/logs/track_a_s6_leakage_audit.log`. It usually means a banned field like `business.stars` was detected in the feature space.
*   **Memory Issues**: Track A processes large volumes of text. If you run out of memory, adjust `eda.sentiment_sample_size` in `configs/track_a.yaml` to a smaller value.
*   **Missing Dependencies**: Ensure you are running from the repository root to allow `python -m` to resolve the `src` package.

---
*Last Updated: 2026-03-12*
