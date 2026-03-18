"""Stage 5 — Imbalance analysis (Gini / Lorenz curves) for Track E."""

from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.config import load_config
from src.eda.track_e.common import (
    ensure_output_dirs,
    load_parquet,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

logger = logging.getLogger(__name__)


def gini(values: np.ndarray) -> float:
    """Compute the Gini coefficient for a 1-D array of non-negative values."""
    arr = np.array(values, dtype=float)
    if arr.size == 0:
        return 0.0
    total = arr.sum()
    if total <= 0:
        return 0.0
    sorted_v = np.sort(arr)
    n = len(sorted_v)
    index = np.arange(1, n + 1)
    raw = (2 * np.sum(index * sorted_v) / (n * total)) - (n + 1) / n
    clipped = max(0.0, min(1.0, float(raw)))
    return clipped


def compute_imbalance(
    coverage_df: pd.DataFrame,
    subgroup_type: str,
    metric: str,
    top_pct: float,
    bottom_pct: float,
) -> dict[str, Any] | None:
    """Compute imbalance metrics for a given subgroup dimension and metric."""
    subset = coverage_df.loc[coverage_df["subgroup_type"] == subgroup_type]
    if subset.empty or metric not in subset.columns:
        return None
    values = subset[metric].dropna().to_numpy(dtype=float)
    if values.size == 0:
        return None

    total = values.sum()
    if total <= 0:
        top_share = 0.0
        bottom_share = 0.0
    else:
        def _share(pct: float, reverse: bool = False) -> float:
            pct = max(0.0, min(100.0, pct))
            if pct == 0.0:
                return 0.0
            k = max(1, math.ceil(len(values) * pct / 100.0))
            selected = np.sort(values)
            if reverse:
                selected = selected[::-1]
            selected = selected[:k]
            return float(selected.sum() / total)

        top_share = _share(top_pct, reverse=True)
        bottom_share = _share(bottom_pct, reverse=False)

    gini_value = gini(values)
    if gini_value > 0.8:
        logger.warning(
            "High Gini (>0.8) for %s / %s: %.3f", subgroup_type, metric, gini_value
        )

    return {
        "subgroup_type": subgroup_type,
        "metric": metric,
        "gini_coefficient": gini_value,
        "top_pct_share": top_share,
        "bottom_pct_share": bottom_share,
        "subgroup_count": int(values.size),
    }


def _plot_lorenz_curve(coverage_df: pd.DataFrame, path: Path) -> None:
    dims = coverage_df["subgroup_type"].dropna().unique().tolist()
    if not dims:
        save_placeholder_figure(
            path,
            title="Track E Gini Lorenz Curve",
            message="No subgroup data available",
        )
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", label="Equality")
    plotted = False
    for dim in dims:
        values = coverage_df.loc[coverage_df["subgroup_type"] == dim, "review_count"]
        values = values.dropna().to_numpy(dtype=float)
        if values.size == 0 or values.sum() <= 0:
            continue
        sorted_v = np.sort(values)
        cum_share = np.cumsum(sorted_v) / sorted_v.sum()
        population = np.arange(1, len(sorted_v) + 1) / len(sorted_v)
        ax.plot(
            np.concatenate(([0], population)),
            np.concatenate(([0], cum_share)),
            label=str(dim),
        )
        plotted = True

    if not plotted:
        save_placeholder_figure(
            path,
            title="Track E Gini Lorenz Curve",
            message="Insufficient review_count data",
        )
        plt.close(fig)
        return

    ax.set_title("Lorenz Curve by Subgroup Dimension")
    ax.set_xlabel("Cumulative Share of Subgroups")
    ax.set_ylabel("Cumulative Share of Reviews")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, linestyle=":", alpha=0.5)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def _plot_gini_bars(records: list[dict[str, Any]], path: Path) -> None:
    if not records:
        save_placeholder_figure(
            path,
            title="Gini by Dimension",
            message="No imbalance records available",
        )
        return

    df = pd.DataFrame(records)
    df["label"] = df["subgroup_type"].astype(str) + " (" + df["metric"].astype(str) + ")"
    fig, ax = plt.subplots(figsize=(8, max(4, len(df) * 0.4)))
    ax.barh(df["label"], df["gini_coefficient"], color="steelblue")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Gini Coefficient")
    ax.set_title("Gini by Dimension and Metric")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)


def run(config: dict[str, Any]) -> None:
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    imbalance_cfg = config.get("imbalance", {})
    top_pct = float(imbalance_cfg.get("gini_top_pct", 10))
    bottom_pct = float(imbalance_cfg.get("gini_bottom_pct", 10))

    coverage_path = paths.tables_dir / "track_e_s2_coverage_by_subgroup.parquet"
    if not coverage_path.exists():
        raise FileNotFoundError(
            f"Stage 2 coverage data missing: {coverage_path}"
        )

    coverage_df = load_parquet(coverage_path)
    records: list[dict[str, Any]] = []
    metrics = ["review_count", "business_count"]
    subgroup_types = coverage_df["subgroup_type"].dropna().unique().tolist()
    for subgroup_type in sorted(subgroup_types):
        for metric in metrics:
            entry = compute_imbalance(coverage_df, subgroup_type, metric, top_pct, bottom_pct)
            if entry is not None:
                records.append(entry)

    if records:
        imbalance_df = pd.DataFrame(records)
    else:
        imbalance_df = pd.DataFrame(
            columns=[
                "subgroup_type",
                "metric",
                "gini_coefficient",
                "top_pct_share",
                "bottom_pct_share",
                "subgroup_count",
            ]
        )

    out_table = paths.tables_dir / "track_e_s5_imbalance_report.parquet"
    write_parquet(imbalance_df, out_table)

    _plot_lorenz_curve(coverage_df, paths.figures_dir / "track_e_s5_lorenz_curve.png")
    _plot_gini_bars(records, paths.figures_dir / "track_e_s5_gini_by_dimension.png")

    logger.info("Stage 5 complete with %d imbalance records.", len(records))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    parser = argparse.ArgumentParser(description="Track E Stage 5 — imbalance analysis")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    args = parser.parse_args()
    cfg = load_config(args.config)
    run(cfg)
