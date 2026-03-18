"""Stage 2: D1 business cold-start cohort construction."""

from __future__ import annotations

import argparse
import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import (
    assign_business_cohort_label,
    ensure_output_dirs,
    load_parquet,
    load_track_a_splits,
    primary_category,
    resolve_paths,
)

logger = logging.getLogger(__name__)


def build_business_cold_start_cohort(
    reviews: pd.DataFrame,
    business_universe: pd.DataFrame,
    as_of_dates: list[str],
    thresholds: dict[str, int],
    recency_windows: list[int],
) -> pd.DataFrame:
    """Materialize D1 business cohorts at each as-of date."""
    reviews = reviews.copy()
    if not reviews.empty:
        reviews["review_date"] = pd.to_datetime(reviews["review_date"])
        reviews["first_review_date"] = reviews.groupby("business_id")["review_date"].transform("min")

    business_universe = business_universe.copy()
    business_universe["primary_category"] = business_universe["categories"].map(primary_category)

    cohort_frames: list[pd.DataFrame] = []
    for as_of_value in as_of_dates:
        as_of_date = pd.Timestamp(as_of_value)
        prior = reviews.loc[reviews["review_date"] < as_of_date].copy()
        prior_summary = (
            prior.groupby("business_id", as_index=False)
            .agg(
                prior_review_count=("review_id", "count"),
                first_seen_date=("review_date", "min"),
            )
        )
        cohort = business_universe.merge(prior_summary, on="business_id", how="left")
        cohort["as_of_date"] = as_of_date.normalize()
        cohort["prior_review_count"] = cohort["prior_review_count"].fillna(0).astype(int)
        cohort["cohort_label"] = cohort["prior_review_count"].map(
            lambda value: assign_business_cohort_label(int(value), thresholds)
        )
        for window in recency_windows:
            col = f"seen_within_{int(window)}d"
            cohort[col] = (
                cohort["first_seen_date"].notna()
                & ((cohort["as_of_date"] - pd.to_datetime(cohort["first_seen_date"])).dt.days <= int(window))
            )
        cohort["subtrack"] = "D1"
        cohort_frames.append(cohort)

    if not cohort_frames:
        return pd.DataFrame()

    return pd.concat(cohort_frames, ignore_index=True)


def summarize_cohorts(cohort_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate D1 cohort sizes by date and label."""
    if cohort_df.empty:
        return pd.DataFrame(columns=["subtrack", "as_of_date", "cohort_label", "business_count"])
    return (
        cohort_df.groupby(["subtrack", "as_of_date", "cohort_label"], as_index=False)
        .agg(business_count=("business_id", "count"))
        .sort_values(["as_of_date", "cohort_label"])
    )


def plot_cohort_sizes(summary_df: pd.DataFrame, out_path) -> None:
    """Plot D1 cohort sizes by as-of date."""
    if summary_df.empty:
        logger.warning("No cohort rows available for D1 size plot.")
        return
    pivot = summary_df.pivot(index="cohort_label", columns="as_of_date", values="business_count").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot.plot(kind="bar", ax=ax)
    ax.set_xlabel("D1 Cohort Label")
    ax.set_ylabel("Business Count")
    ax.set_title("Track D: Business Cold-Start Cohort Sizes")
    ax.legend(title="As-of date")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2: Business Cold Start")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    reviews = load_parquet(
        paths.review_fact_path,
        """
        SELECT review_id, business_id, review_date
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    if paths.business_path.is_file():
        business_universe = load_parquet(
            paths.business_path,
            """
            SELECT business_id, city, state, categories
            FROM read_parquet(?)
            """,
            [str(paths.business_path)],
        )
    else:
        business_universe = load_parquet(
            paths.review_fact_path,
            """
            SELECT DISTINCT business_id, city, state, categories
            FROM read_parquet(?)
            """,
            [str(paths.review_fact_path)],
        )

    t1, t2, _ = load_track_a_splits(config, paths.tables_dir)
    cohort_df = build_business_cold_start_cohort(
        reviews=reviews,
        business_universe=business_universe,
        as_of_dates=[t1, t2],
        thresholds=config["cold_start"]["d1_thresholds"],
        recency_windows=list(config["cold_start"]["d1_recency_windows_days"]),
    )
    summary_df = summarize_cohorts(cohort_df)

    cohort_out = paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet"
    cohort_df.to_parquet(cohort_out, index=False)
    logger.info("Wrote %s (%d rows)", cohort_out, len(cohort_df))

    summary_out = paths.tables_dir / "track_d_s2_business_cohort_size_by_threshold.parquet"
    summary_df.to_parquet(summary_out, index=False)
    logger.info("Wrote %s (%d rows)", summary_out, len(summary_df))

    plot_cohort_sizes(summary_df, paths.figures_dir / "track_d_s2_business_cohort_sizes.png")
    logger.info("Stage 2 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
