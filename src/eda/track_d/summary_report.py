"""Stage 9: Consolidated markdown summary for Track D."""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import ensure_output_dirs, load_parquet, resolve_paths

logger = logging.getLogger(__name__)


def _safe_read(path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    return load_parquet(path)


def build_summary_markdown(
    stage2_df: pd.DataFrame | None,
    stage3_df: pd.DataFrame | None,
    stage5_df: pd.DataFrame | None,
    stage6_df: pd.DataFrame | None,
    stage7_df: pd.DataFrame | None,
    stage8_df: pd.DataFrame | None,
) -> str:
    """Render a concise Track D markdown summary."""
    lines = ["# Track D EDA Summary", ""]

    lines.extend(["## D1 Business Cold Start", ""])
    if stage2_df is not None and not stage2_df.empty:
        d1_sizes = (
            stage2_df.groupby("cohort_label", as_index=False)
            .agg(business_count=("business_id", "count"))
            .sort_values("business_count", ascending=False)
        )
        for row in d1_sizes.itertuples(index=False):
            lines.append(f"- `{row.cohort_label}`: {int(row.business_count):,} businesses across as-of dates.")
    else:
        lines.append("- Stage 2 artifact is missing.")

    if stage3_df is not None and not stage3_df.empty:
        coverage = stage3_df.loc[stage3_df["feature_name"] == "attribute_count"]
        if not coverage.empty:
            best = coverage.sort_values("coverage_rate", ascending=False).iloc[0]
            lines.append(
                f"- Best static D1 feature coverage: `{best['segment_label']}` attribute_count at {float(best['coverage_rate']):.1%}."
            )
    else:
        lines.append("- Stage 3 artifact is missing.")

    lines.extend(["", "## D2 User Cold Start", ""])
    if stage5_df is not None and not stage5_df.empty:
        d2_sizes = (
            stage5_df.groupby("cohort_label", as_index=False)
            .agg(user_count=("user_id", "count"))
            .sort_values("user_count", ascending=False)
        )
        for row in d2_sizes.itertuples(index=False):
            lines.append(f"- `{row.cohort_label}`: {int(row.user_count):,} users across as-of dates.")
    else:
        lines.append("- Stage 5 artifact is missing.")

    if stage6_df is not None and not stage6_df.empty:
        best = stage6_df.sort_values("coverage_rate", ascending=False).iloc[0]
        lines.append(
            f"- Strongest D2 warm-up feature coverage: `{best['segment_label']}` `{best['feature_name']}` at {float(best['coverage_rate']):.1%}."
        )
    else:
        lines.append("- Stage 6 artifact is missing.")

    lines.extend(["", "## Evaluation Cohorts", ""])
    if stage7_df is not None and not stage7_df.empty:
        for row in stage7_df.itertuples(index=False):
            lines.append(
                f"- {row.subtrack}: `{row.cohort_label}` entity_count={int(row.entity_count):,}, "
                f"label_rate={float(row.label_rate):.1%}, avg_candidate_set_size={float(row.avg_candidate_set_size):.1f}."
            )
    else:
        lines.append("- Stage 7 artifact is missing.")

    lines.extend(["", "## Leakage Gate", ""])
    if stage8_df is not None and not stage8_df.empty:
        failures = stage8_df.loc[stage8_df["status"] == "FAIL"]
        if failures.empty:
            lines.append("- Stage 8 passed with zero FAIL findings.")
        else:
            lines.append("- Stage 8 reported blocking failures:")
            for row in failures.itertuples(index=False):
                lines.append(f"  - `{row.finding_name}`: {row.detail}")
    else:
        lines.append("- Stage 8 artifact is missing.")

    lines.extend(
        [
            "",
            "## Recommendation",
            "- Keep D1 and D2 separate in any downstream modeling notebook or training pipeline.",
            "- Do not proceed to modeling if the leakage gate reports any FAIL findings.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 9: Summary Report")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    summary = build_summary_markdown(
        _safe_read(paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet"),
        _safe_read(paths.tables_dir / "track_d_s3_business_signal_summary.parquet"),
        _safe_read(paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet"),
        _safe_read(paths.tables_dir / "track_d_s6_user_feature_coverage.parquet"),
        _safe_read(paths.tables_dir / "track_d_s7_eval_cohort_summary.parquet"),
        _safe_read(paths.tables_dir / "track_d_s8_leakage_report.parquet"),
    )

    out = paths.tables_dir / "track_d_s9_eda_summary.md"
    out.write_text(summary, encoding="utf-8")
    logger.info("Wrote %s", out)
    logger.info("Stage 9 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
