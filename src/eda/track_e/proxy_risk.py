"""Stage 6 — Proxy risk analysis for Track E."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr

from src.common.config import load_config
from src.eda.track_e.common import (
    ensure_output_dirs,
    load_parquet,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

logger = logging.getLogger(__name__)


def _detect_stars_column(review_path: Path) -> str:
    con = duckdb.connect()
    try:
        schema_df = con.execute(
            "SELECT column_name FROM parquet_schema(?)", [str(review_path)]
        ).fetchdf()
    finally:
        con.close()
    columns = {name for name in schema_df["column_name"].tolist()}
    if "stars" in columns:
        return "stars"
    if "review_stars" in columns:
        return "review_stars"
    raise KeyError(
        "review_fact.parquet missing both 'stars' and 'review_stars'; "
        f"available columns: {sorted(columns)}"
    )


def _build_business_features(review_path: Path) -> pd.DataFrame:
    if not review_path.is_file():
        logger.warning("review_fact.parquet not found at %s; proxy features will be empty.", review_path)
        return pd.DataFrame(columns=["business_id"])

    stars_col = _detect_stars_column(review_path)
    sql = (
        "SELECT "
        "business_id, "
        "COUNT(*) AS review_count_asof, "
        f"AVG({stars_col}) AS avg_stars_asof, "
        "AVG(text_word_count) AS text_length_mean_asof, "
        "AVG(useful) AS useful_mean_asof "
        "FROM read_parquet(?) "
        "GROUP BY business_id"
    )
    features = load_parquet(review_path, sql=sql, params=[str(review_path)])
    logger.info("Computed proxy candidate features for %d businesses", len(features))
    return features


def _plot_proxy_heatmap(df: pd.DataFrame, path: Path) -> None:
    if df.empty:
        save_placeholder_figure(
            path,
            title="Proxy correlation heatmap",
            message="No proxy correlations available",
        )
        return

    pivot = df.pivot(index="feature", columns="subgroup_indicator", values="correlation")
    pivot = pivot.fillna(0.0)
    n_cols = max(len(pivot.columns), 1)
    n_rows = max(len(pivot.index), 1)
    fig, ax = plt.subplots(
        figsize=(max(6, n_cols * 0.6 + 2), max(4, n_rows * 0.6 + 1)),
    )
    im = ax.imshow(pivot.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(n_cols))
    ax.set_yticks(np.arange(n_rows))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right", fontsize=8)
    ax.set_yticklabels(pivot.index, fontsize=9)
    ax.set_xlabel("Subgroup indicator")
    ax.set_ylabel("Feature")
    ax.set_title("Proxy correlations (higher magnitude indicates stronger subgroup signal)")
    fig.colorbar(im, ax=ax, label="Correlation")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote heatmap %s", path)


def compute_proxy_correlations(
    features_df: pd.DataFrame,
    subgroup_defs: pd.DataFrame,
    candidate_features: Sequence[str],
    correlation_threshold: float,
    min_group_size: int,
) -> pd.DataFrame:
    """Compute point-biserial correlations between features and subgroup indicators."""
    records: list[dict[str, object]] = []
    if features_df.empty or subgroup_defs.empty:
        return pd.DataFrame(records, columns=[
            "feature",
            "subgroup_indicator",
            "correlation",
            "p_value",
            "is_proxy_risk",
        ])

    merged = features_df.merge(subgroup_defs, on="business_id", how="inner")
    subgroup_columns = [col for col in subgroup_defs.columns if col != "business_id"]

    for dim in subgroup_columns:
        if dim not in merged.columns:
            continue
        group_counts = merged.groupby(dim)["business_id"].nunique()
        valid_values = [val for val, count in group_counts.items() if count >= min_group_size]
        if not valid_values:
            continue
        for value in valid_values:
            indicator = (merged[dim].astype(str) == str(value)).astype(int)
            if indicator.sum() < 1 or indicator.sum() == len(indicator):
                continue
            for feature in candidate_features:
                if feature not in merged.columns:
                    continue
                feature_values = merged[feature]
                if feature_values.nunique(dropna=True) <= 1:
                    continue
                try:
                    correlation, p_value = pointbiserialr(indicator, feature_values)
                except ValueError:
                    continue
                if np.isnan(correlation) or np.isnan(p_value):
                    continue
                correlation = float(np.clip(correlation, -1.0, 1.0))
                p_value = float(min(max(p_value, 0.0), 1.0))
                records.append(
                    {
                        "feature": feature,
                        "subgroup_indicator": f"{dim}_{value}",
                        "correlation": correlation,
                        "p_value": p_value,
                        "is_proxy_risk": abs(correlation) > correlation_threshold and p_value < 0.05,
                    }
                )
    if not records:
        return pd.DataFrame(
            columns=[
                "feature",
                "subgroup_indicator",
                "correlation",
                "p_value",
                "is_proxy_risk",
            ]
        )
    return pd.DataFrame(records)


def run(config: dict[str, object]) -> None:
    """Execute Stage 6: proxy risk analysis."""
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    proxy_cfg = config.get("proxy", {})
    candidate_features = proxy_cfg.get("candidate_features", [])
    correlation_threshold = float(proxy_cfg.get("correlation_threshold", 0.3))
    min_group_size = int(config.get("subgroups", {}).get("min_group_size", 10))

    features_df = _build_business_features(paths.review_fact_path)

    subgroup_path = paths.tables_dir / "track_e_s1_subgroup_definitions.parquet"
    if not subgroup_path.is_file():
        raise FileNotFoundError(
            f"Stage 1 output not found at {subgroup_path}; run Stage 1 first."
        )
    subgroup_defs = load_parquet(subgroup_path)
    logger.info("Loaded subgroup definitions: %d businesses", len(subgroup_defs))

    user_path = paths.user_path
    if user_path.is_file():
        user_df = load_parquet(
            user_path,
            sql="SELECT user_id, review_count, average_stars FROM read_parquet(?)",
            params=[str(user_path)],
        )
        logger.info(
            "Read %d user records for audit purposes; user-level proxies are not used in this release.",
            len(user_df),
        )
    else:
        logger.warning("user.parquet not found at %s; skipping user-level proxy scan.", user_path)

    proxy_df = compute_proxy_correlations(
        features_df=features_df,
        subgroup_defs=subgroup_defs,
        candidate_features=candidate_features,
        correlation_threshold=correlation_threshold,
        min_group_size=min_group_size,
    )
    proxy_path = paths.tables_dir / "track_e_s6_proxy_correlations.parquet"
    write_parquet(proxy_df, proxy_path)
    logger.info("Proxy correlations table contains %d rows", len(proxy_df))

    heatmap_path = paths.figures_dir / "track_e_s6_proxy_heatmap.png"
    _plot_proxy_heatmap(proxy_df, heatmap_path)

    logger.info("Stage 6 complete.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 6 — Track E proxy risk analysis")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = _parse_args()
    cfg = load_config(args.config)
    run(cfg)
