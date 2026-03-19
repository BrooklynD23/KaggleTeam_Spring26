"""Stage 8: Consolidated markdown summary for Track B."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_b.common import (
    TrackBPaths,
    ensure_output_dirs,
    load_snapshot_metadata,
    resolve_paths,
)

logger = logging.getLogger(__name__)


def _read_parquet_if_present(path: Path, config: dict) -> pd.DataFrame | None:
    """Read a parquet artifact if it exists."""
    if not path.is_file():
        return None
    pq_str = str(path).replace("\\", "/")
    con = connect_duckdb(config)
    try:
        return con.execute(f"SELECT * FROM read_parquet('{pq_str}')").fetchdf()
    finally:
        con.close()


def _pick_top_correlates(feature_df: pd.DataFrame | None) -> list[str]:
    """Return compact bullets for the strongest correlates per age bucket."""
    if feature_df is None or feature_df.empty:
        return ["Feature-correlate artifact missing."]

    subset = feature_df.loc[
        feature_df["metric_value"].notna()
        & feature_df["feature_kind"].isin(["numeric", "binary"])
    ].copy()
    if subset.empty:
        return ["No numeric or binary correlate rows were available."]

    subset["abs_metric"] = subset["metric_value"].abs()
    strongest = (
        subset.sort_values(["age_bucket", "abs_metric"], ascending=[True, False])
        .groupby("age_bucket", as_index=False)
        .head(1)
    )
    return [
        (
            f"{row.age_bucket}: strongest {row.feature_name} "
            f"({row.metric_name}={row.metric_value:.4f})"
        )
        for row in strongest.itertuples(index=False)
    ]


def build_summary_markdown(
    metadata: dict[str, str],
    stage1_df: pd.DataFrame | None,
    stage2_df: pd.DataFrame | None,
    stage3_business_df: pd.DataFrame | None,
    stage3_category_df: pd.DataFrame | None,
    stage4_summary_df: pd.DataFrame | None,
    stage5_df: pd.DataFrame | None,
    stage6_pairwise_df: pd.DataFrame | None,
    stage6_listwise_df: pd.DataFrame | None,
    stage7_df: pd.DataFrame | None,
) -> str:
    """Render the Track B Stage 8 markdown summary."""
    lines = [
        "# Track B EDA Summary",
        "",
        f"- Snapshot reference date: `{metadata['snapshot_reference_date']}`",
        f"- Dataset release tag: `{metadata['dataset_release_tag']}`",
        "",
        "## Stage 1-2 Snapshot and Age Framing",
    ]

    if stage1_df is not None and not stage1_df.empty:
        zero_row = stage1_df.loc[stage1_df["useful"] == 0]
        if not zero_row.empty:
            zero_count = int(zero_row.iloc[0]["review_count"])
            lines.append(f"- Reviews with `useful = 0`: {zero_count:,}")
    else:
        lines.append("- Stage 1 usefulness-distribution artifact missing.")

    if stage2_df is not None and not stage2_df.empty:
        strongest_age = stage2_df.sort_values("mean_useful", ascending=False).iloc[0]
        lines.append(
            "- Highest mean-useful age bucket: "
            f"`{strongest_age['age_bucket']}` "
            f"(mean useful `{strongest_age['mean_useful']:.4f}`)"
        )
    else:
        lines.append("- Stage 2 age-effect summary artifact missing.")

    lines.extend(["", "## Stage 3-4 Grouping and Labels"])
    if stage3_business_df is not None and not stage3_business_df.empty:
        business_groups = int(stage3_business_df["qualifies"].sum())
        lines.append(f"- Qualifying business x age groups: {business_groups:,}")
    else:
        lines.append("- Stage 3 business-group artifact missing.")

    if stage3_category_df is not None and not stage3_category_df.empty:
        category_groups = int(stage3_category_df["qualifies"].sum())
        lines.append(f"- Qualifying category x age groups: {category_groups:,}")
    else:
        lines.append("- Stage 3 category-group artifact missing.")

    if stage4_summary_df is not None and not stage4_summary_df.empty:
        primary = stage4_summary_df.loc[stage4_summary_df["recommended_primary"]]
        secondary = stage4_summary_df.loc[stage4_summary_df["recommended_secondary"]]
        if not primary.empty:
            lines.append(
                f"- Recommended primary label: `{primary.iloc[0]['scheme_name']}`"
            )
        if not secondary.empty:
            lines.append(
                f"- Recommended secondary label: `{secondary.iloc[0]['scheme_name']}`"
            )
    else:
        lines.append("- Stage 4 label-scheme summary artifact missing.")

    lines.extend(["", "## Stage 5-6 Modeling Feasibility"])
    for bullet in _pick_top_correlates(stage5_df):
        lines.append(f"- {bullet}")

    if stage6_pairwise_df is not None and not stage6_pairwise_df.empty:
        overall_pairwise = stage6_pairwise_df.loc[
            stage6_pairwise_df["age_bucket"] == "ALL"
        ]
        if not overall_pairwise.empty:
            for row in overall_pairwise.itertuples(index=False):
                lines.append(
                    f"- {row.group_type}: raw pairs={int(row.raw_pairs):,}, "
                    f"tied pairs={int(row.tied_pairs):,}, "
                    f"valid pairs={int(row.valid_pairs):,}, "
                    f"signoff={bool(row.feasibility_signoff)}"
                )
    else:
        lines.append("- Stage 6 pairwise-feasibility artifact missing.")

    if stage6_listwise_df is not None and not stage6_listwise_df.empty:
        overall_listwise = stage6_listwise_df.loc[
            stage6_listwise_df["age_bucket"] == "ALL"
        ]
        if not overall_listwise.empty:
            for row in overall_listwise.itertuples(index=False):
                lines.append(
                    f"- {row.group_type}: avg list length={row.avg_list_length:.2f}, "
                    f"non-degenerate top-decile groups={row.pct_non_degenerate_top_decile:.4f}"
                )
    else:
        lines.append("- Stage 6 listwise-feasibility artifact missing.")

    lines.extend(["", "## Stage 7 Scope Check"])
    if stage7_df is not None and not stage7_df.empty:
        failures = stage7_df.loc[stage7_df["status"] == "FAIL"]
        if failures.empty:
            lines.append("- Stage 7 passed with no leakage or scope violations.")
        else:
            lines.append("- Stage 7 reported failures:")
            for row in failures.itertuples(index=False):
                lines.append(
                    f"  - `{row.finding_name}` in `{row.artifact_path}`: {row.detail}"
                )
    else:
        lines.append("- Stage 7 leakage-scope report artifact missing.")

    lines.extend(
        [
            "",
            "## Recommendation",
            "- Proceed only if Stage 7 remains clean and the preferred label scheme "
            "retains enough net valid pairs after tie removal.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 8: Summary Report")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    metadata = load_snapshot_metadata(paths)

    stage1_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s1_useful_vote_distribution.parquet", config
    )
    stage2_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s2_age_effect_summary.parquet", config
    )
    stage3_business_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s3_group_sizes_by_business_age.parquet", config
    )
    stage3_category_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s3_group_sizes_by_category_age.parquet", config
    )
    stage4_summary_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s4_label_scheme_summary.parquet", config
    )
    stage5_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s5_feature_correlates.parquet", config
    )
    stage6_pairwise_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s6_pairwise_stats.parquet", config
    )
    stage6_listwise_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s6_listwise_stats.parquet", config
    )
    stage7_df = _read_parquet_if_present(
        paths.tables_dir / "track_b_s7_leakage_scope_report.parquet", config
    )

    summary = build_summary_markdown(
        metadata=metadata,
        stage1_df=stage1_df,
        stage2_df=stage2_df,
        stage3_business_df=stage3_business_df,
        stage3_category_df=stage3_category_df,
        stage4_summary_df=stage4_summary_df,
        stage5_df=stage5_df,
        stage6_pairwise_df=stage6_pairwise_df,
        stage6_listwise_df=stage6_listwise_df,
        stage7_df=stage7_df,
    )

    out = paths.tables_dir / "track_b_s8_eda_summary.md"
    out.write_text(summary, encoding="utf-8")
    logger.info("Wrote %s", out)
    logger.info("Stage 8 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
