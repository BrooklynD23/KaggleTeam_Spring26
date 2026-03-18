"""Stage 5: D2 user cold-start cohort construction."""

from __future__ import annotations

import argparse
import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import assign_user_cohort_label, ensure_output_dirs, load_parquet, load_track_a_splits, resolve_paths

logger = logging.getLogger(__name__)


def build_user_cold_start_cohort(
    review_df: pd.DataFrame,
    tip_df: pd.DataFrame,
    as_of_dates: list[str],
    primary_k: int,
) -> pd.DataFrame:
    """Build D2 cohorts from prior reviews plus prior tips."""
    all_user_ids = sorted(set(review_df["user_id"].dropna().tolist()) | set(tip_df["user_id"].dropna().tolist()))
    frames: list[pd.DataFrame] = []

    review_df = review_df.copy()
    review_df["review_date"] = pd.to_datetime(review_df["review_date"])
    tip_df = tip_df.copy()
    if not tip_df.empty:
        tip_df["tip_date"] = pd.to_datetime(tip_df["tip_date"])

    primary_map = {0: "zero_history", 1: "first_interaction", 3: "early"}
    primary_label = primary_map.get(primary_k, "zero_history")

    for as_of_value in as_of_dates:
        as_of_date = pd.Timestamp(as_of_value)
        review_counts = (
            review_df.loc[review_df["review_date"] < as_of_date]
            .groupby("user_id", as_index=False)
            .agg(prior_review_count=("review_id", "count"))
        )
        tip_counts = (
            tip_df.loc[tip_df["tip_date"] < as_of_date].groupby("user_id", as_index=False).size().rename(columns={"size": "prior_tip_count"})
            if not tip_df.empty
            else pd.DataFrame(columns=["user_id", "prior_tip_count"])
        )
        cohort = pd.DataFrame({"user_id": all_user_ids})
        cohort = cohort.merge(review_counts, on="user_id", how="left")
        cohort = cohort.merge(tip_counts, on="user_id", how="left")
        cohort["prior_review_count"] = cohort["prior_review_count"].fillna(0).astype(int)
        cohort["prior_tip_count"] = cohort["prior_tip_count"].fillna(0).astype(int)
        cohort["prior_total_interaction_count"] = cohort["prior_review_count"] + cohort["prior_tip_count"]
        cohort["cohort_label"] = cohort["prior_total_interaction_count"].map(assign_user_cohort_label)
        cohort["is_primary_cohort"] = cohort["cohort_label"].eq(primary_label)
        cohort["as_of_date"] = as_of_date.normalize()
        cohort["subtrack"] = "D2"
        frames.append(cohort)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def plot_user_activity_ramp(cohort_df: pd.DataFrame, out_path) -> None:
    """Plot the CDF of prior total interactions at each as-of date."""
    if cohort_df.empty:
        logger.warning("No user cohort rows available for activity ramp plot.")
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    for as_of_date, chunk in cohort_df.groupby("as_of_date", sort=True):
        values = np.sort(chunk["prior_total_interaction_count"].to_numpy())
        cdf = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, cdf, label=str(pd.Timestamp(as_of_date).date()))
    ax.set_xlabel("Prior Total Interaction Count")
    ax.set_ylabel("CDF")
    ax.set_title("Track D: User Activity Ramp-Up")
    ax.set_xscale("symlog")
    ax.grid(alpha=0.3)
    ax.legend(title="As-of date")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out_path)


def plot_first_k_behavior(cohort_df: pd.DataFrame, out_path) -> None:
    """Plot D2 cohort sizes by label."""
    if cohort_df.empty:
        logger.warning("No user cohort rows available for first-K behavior plot.")
        return
    summary = cohort_df.groupby(["cohort_label", "as_of_date"], as_index=False).agg(user_count=("user_id", "count"))
    pivot = summary.pivot(index="cohort_label", columns="as_of_date", values="user_count").fillna(0)
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_xlabel("D2 Cohort Label")
    ax.set_ylabel("User Count")
    ax.set_title("Track D: D2 Cohort Sizes")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 5: User Cold Start")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    review_df = load_parquet(
        paths.review_fact_path,
        """
        SELECT review_id, user_id, review_date
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    tip_df = (
        load_parquet(paths.tip_path, "SELECT user_id, tip_date FROM read_parquet(?) WHERE tip_date IS NOT NULL", [str(paths.tip_path)])
        if paths.tip_path.is_file()
        else pd.DataFrame(columns=["user_id", "tip_date"])
    )

    t1, t2, _ = load_track_a_splits(config, paths.tables_dir)
    cohort_df = build_user_cold_start_cohort(
        review_df,
        tip_df,
        [t1, t2],
        int(config["cold_start"]["d2_primary_k"]),
    )
    out = paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet"
    cohort_df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(cohort_df))

    plot_user_activity_ramp(cohort_df, paths.figures_dir / "track_d_s5_user_activity_ramp.png")
    plot_first_k_behavior(cohort_df, paths.figures_dir / "track_d_s5_first_k_review_behavior.png")
    logger.info("Stage 5 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
