"""Track E Stage 4 — Usefulness Disparity by Subgroup.

Computes useful-vote disparities across subgroups to identify
"visibility deserts" — subgroups where reviews receive disproportionately
few useful votes relative to the overall dataset baseline.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import load_config
from src.eda.track_e.common import (
    enforce_min_group_size,
    ensure_output_dirs,
    load_parquet,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

logger = logging.getLogger(__name__)

_SUBGROUP_DIMS = ["city", "primary_category", "price_tier", "review_volume_tier"]


# ---------------------------------------------------------------------------
# Core logic — importable by tests
# ---------------------------------------------------------------------------


def compute_usefulness_stats(
    reviews_with_defs: pd.DataFrame,
    dimension: str,
    min_group_size: int,
) -> pd.DataFrame:
    """Compute useful-vote statistics for each value of a subgroup dimension.

    Args:
        reviews_with_defs: DataFrame containing a 'useful' column and the
            dimension column (e.g. 'city').
        dimension: Column name to group by.
        min_group_size: Minimum review_count to retain a group.

    Returns:
        DataFrame with columns: subgroup_type, subgroup_value, review_count,
        mean_useful, median_useful, pct_zero_useful.
    """
    if dimension not in reviews_with_defs.columns or reviews_with_defs.empty:
        return pd.DataFrame(
            columns=[
                "subgroup_type", "subgroup_value", "review_count",
                "mean_useful", "median_useful", "pct_zero_useful",
            ]
        )

    grp = reviews_with_defs.groupby(dimension, dropna=False)["useful"]
    stats = pd.DataFrame(
        {
            "review_count": grp.count(),
            "mean_useful": grp.mean(),
            "median_useful": grp.median(),
            "pct_zero_useful": grp.apply(lambda s: (s == 0).sum() / max(len(s), 1)),
        }
    ).reset_index()
    stats.columns = ["subgroup_value", "review_count", "mean_useful", "median_useful", "pct_zero_useful"]
    stats.insert(0, "subgroup_type", dimension)
    stats["subgroup_value"] = stats["subgroup_value"].astype(str)
    stats["review_count"] = stats["review_count"].astype(int)

    return enforce_min_group_size(stats, "review_count", min_group_size)


def flag_visibility_deserts(
    stats_df: pd.DataFrame,
    overall_pct_zero: float,
) -> pd.DataFrame:
    """Add an is_visibility_desert boolean column.

    A subgroup is a visibility desert when its pct_zero_useful exceeds
    2× the dataset-wide rate of zero-useful reviews.

    Args:
        stats_df: Output of compute_usefulness_stats (one or more dims).
        overall_pct_zero: Dataset-wide fraction of reviews with useful == 0.

    Returns:
        New DataFrame with is_visibility_desert column added.
    """
    threshold = 2.0 * overall_pct_zero
    flagged = stats_df.copy()
    flagged["is_visibility_desert"] = flagged["pct_zero_useful"] > threshold
    deserts = flagged.loc[flagged["is_visibility_desert"]]
    if not deserts.empty:
        desert_labels = [
            f"{r.subgroup_type}={r.subgroup_value}" for r in deserts.itertuples()
        ]
        logger.info(
            "Visibility deserts found (pct_zero_useful > 2× baseline=%.3f): %s",
            overall_pct_zero,
            ", ".join(desert_labels),
        )
    else:
        logger.info(
            "No visibility deserts found (baseline pct_zero_useful=%.3f, threshold=%.3f).",
            overall_pct_zero,
            threshold,
        )
    return flagged


def plot_useful_by_subgroup(stats_df: pd.DataFrame, path: Path) -> None:
    """Save a grouped bar chart of mean_useful by subgroup_value per dimension.

    Shows top 5 subgroups per dimension for readability. Visibility deserts
    are annotated with an asterisk (*) in the x-axis tick labels.

    Args:
        stats_df: DataFrame with columns subgroup_type, subgroup_value,
            mean_useful, is_visibility_desert.
        path: Output .png path.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if stats_df.empty or "subgroup_type" not in stats_df.columns:
        save_placeholder_figure(path, "Useful Votes by Subgroup", "No data available")
        return

    dims = stats_df["subgroup_type"].unique().tolist()
    n_dims = len(dims)
    if n_dims == 0:
        save_placeholder_figure(path, "Useful Votes by Subgroup", "No subgroup dimensions found")
        return

    fig, axes = plt.subplots(1, n_dims, figsize=(5 * n_dims, 5), sharey=False)
    if n_dims == 1:
        axes = [axes]

    desert_count = int(stats_df.get("is_visibility_desert", pd.Series(dtype=bool)).sum())
    title_note = f"  (* = visibility desert; {desert_count} found)" if desert_count else ""

    for ax, dim in zip(axes, dims):
        subset = (
            stats_df.loc[stats_df["subgroup_type"] == dim]
            .nlargest(5, "review_count")
            .copy()
        )
        if subset.empty:
            ax.set_title(dim)
            ax.axis("off")
            continue

        is_desert = subset.get("is_visibility_desert", pd.Series(False, index=subset.index))
        labels = [
            f"{v} *" if d else str(v)
            for v, d in zip(subset["subgroup_value"], is_desert)
        ]
        ax.bar(range(len(subset)), subset["mean_useful"], color="steelblue", alpha=0.8)
        ax.set_xticks(range(len(subset)))
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
        ax.set_title(dim, fontsize=10)
        ax.set_ylabel("Mean useful votes")

    fig.suptitle(f"Useful Votes by Subgroup{title_note}", fontsize=11)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote figure %s", path)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------


def run(config: dict[str, Any]) -> None:
    """Execute Stage 4: usefulness disparity analysis.

    Produces:
      - outputs/tables/track_e_s4_usefulness_disparity.parquet
      - outputs/figures/track_e_s4_useful_by_subgroup.png
    """
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    min_group_size = int(config.get("subgroups", {}).get("min_group_size", 10))

    # 1. Load review_fact
    logger.info("Loading review_fact from %s", paths.review_fact_path)
    if paths.review_fact_path.is_file():
        pq_str = str(paths.review_fact_path).replace("\\", "/")
        reviews = load_parquet(
            paths.review_fact_path,
            sql=f"SELECT business_id, user_id, useful FROM read_parquet('{pq_str}')",
        )
    else:
        logger.warning("review_fact.parquet not found — using empty frame.")
        reviews = pd.DataFrame(columns=["business_id", "user_id", "useful"])

    # 2. Load Stage 1 subgroup definitions
    s1_path = paths.tables_dir / "track_e_s1_subgroup_definitions.parquet"
    logger.info("Loading subgroup definitions from %s", s1_path)
    if s1_path.is_file():
        subgroup_defs = load_parquet(s1_path)
    else:
        logger.warning("Subgroup definitions not found at %s — using empty frame.", s1_path)
        subgroup_defs = pd.DataFrame(
            columns=["business_id", "city", "primary_category", "price_tier", "review_volume_tier"]
        )

    # 3. Join reviews to subgroup definitions on business_id
    merged = reviews.merge(subgroup_defs, on="business_id", how="inner")

    # 4. Compute overall pct_zero_useful from full merged dataset
    if merged.empty or "useful" not in merged.columns:
        overall_pct_zero = 0.0
    else:
        overall_pct_zero = float((merged["useful"] == 0).mean())
    logger.info("Overall pct_zero_useful across all reviews: %.4f", overall_pct_zero)

    # 5. Compute stats per dimension
    frames: list[pd.DataFrame] = []
    for dim in _SUBGROUP_DIMS:
        dim_stats = compute_usefulness_stats(merged, dim, min_group_size=min_group_size)
        if not dim_stats.empty:
            frames.append(dim_stats)

    if frames:
        all_stats = pd.concat(frames, ignore_index=True)
    else:
        all_stats = pd.DataFrame(
            columns=[
                "subgroup_type", "subgroup_value", "review_count",
                "mean_useful", "median_useful", "pct_zero_useful",
            ]
        )

    # 6. Flag visibility deserts using the overall rate
    all_stats = flag_visibility_deserts(all_stats, overall_pct_zero)

    # 7. Enforce min_group_size (may already be enforced per dim, but apply globally)
    all_stats = enforce_min_group_size(all_stats, "review_count", min_group_size)

    # 8. Note the key confounder: higher useful votes may reflect traffic/visibility,
    #    not review quality — a business with more views accumulates more useful votes
    #    purely through exposure, independent of review content.
    logger.info(
        "Confounder note: higher mean_useful may reflect business traffic/visibility exposure "
        "rather than review quality differences across subgroups. "
        "Interpret pct_zero_useful and is_visibility_desert with this in mind."
    )

    # 9. Write parquet output
    out_table = paths.tables_dir / "track_e_s4_usefulness_disparity.parquet"
    write_parquet(all_stats, out_table)

    # 10. Plot
    out_fig = paths.figures_dir / "track_e_s4_useful_by_subgroup.png"
    plot_useful_by_subgroup(all_stats, out_fig)

    logger.info("Stage 4 complete.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging as _logging

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Stage 4 — Track E Usefulness Disparity")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    args = parser.parse_args()
    _config = load_config(args.config)
    run(_config)
