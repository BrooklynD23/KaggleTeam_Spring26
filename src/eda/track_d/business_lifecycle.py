"""Stage 1: Business lifecycle and review accrual profiling."""

from __future__ import annotations

import argparse
import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import ensure_output_dirs, load_parquet, primary_category, resolve_paths

logger = logging.getLogger(__name__)


def build_business_lifecycle(reviews: pd.DataFrame) -> pd.DataFrame:
    """Build per-business lifecycle statistics from review history."""
    if reviews.empty:
        return pd.DataFrame(
            columns=[
                "business_id",
                "city",
                "primary_category",
                "first_review_date",
                "last_review_date",
                "total_review_count",
                "days_to_3rd_review",
                "days_to_5th_review",
                "days_to_10th_review",
            ]
        )

    reviews = reviews.copy()
    reviews["review_date"] = pd.to_datetime(reviews["review_date"])
    reviews["primary_category"] = reviews["categories"].map(primary_category)
    reviews = reviews.sort_values(["business_id", "review_date", "review_id"])
    reviews["review_rank"] = reviews.groupby("business_id").cumcount() + 1

    base = (
        reviews.groupby("business_id", as_index=False)
        .agg(
            city=("city", "first"),
            primary_category=("primary_category", "first"),
            first_review_date=("review_date", "min"),
            last_review_date=("review_date", "max"),
            total_review_count=("review_id", "count"),
        )
    )

    nth_dates = (
        reviews.loc[reviews["review_rank"].isin([3, 5, 10]), ["business_id", "review_rank", "review_date"]]
        .drop_duplicates(["business_id", "review_rank"])
        .pivot(index="business_id", columns="review_rank", values="review_date")
        .rename(columns={3: "third_review_date", 5: "fifth_review_date", 10: "tenth_review_date"})
        .reset_index()
    )

    merged = base.merge(nth_dates, on="business_id", how="left")
    for label, date_col in [
        ("days_to_3rd_review", "third_review_date"),
        ("days_to_5th_review", "fifth_review_date"),
        ("days_to_10th_review", "tenth_review_date"),
    ]:
        merged[label] = (
            pd.to_datetime(merged[date_col]) - pd.to_datetime(merged["first_review_date"])
        ).dt.days
    return merged.drop(columns=["third_review_date", "fifth_review_date", "tenth_review_date"], errors="ignore")


def plot_review_accrual_curves(reviews: pd.DataFrame, out_path) -> None:
    """Plot median days-since-first-review by observed review rank."""
    if reviews.empty:
        logger.warning("No review rows available for accrual curve plot.")
        return

    ordered = reviews.copy()
    ordered["review_date"] = pd.to_datetime(ordered["review_date"])
    ordered = ordered.sort_values(["business_id", "review_date", "review_id"])
    ordered["review_rank"] = ordered.groupby("business_id").cumcount() + 1
    ordered["first_review_date"] = ordered.groupby("business_id")["review_date"].transform("min")
    ordered["days_since_first_review"] = (
        ordered["review_date"] - ordered["first_review_date"]
    ).dt.days
    curve = (
        ordered.loc[ordered["review_rank"] <= 10]
        .groupby("review_rank", as_index=False)["days_since_first_review"]
        .median()
    )
    if curve.empty:
        logger.warning("No rows available for review accrual curve plot.")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(curve["review_rank"], curve["days_since_first_review"], marker="o")
    ax.set_xlabel("Observed Review Rank")
    ax.set_ylabel("Median Days Since First Review")
    ax.set_title("Track D: Median Review Accrual Curve")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out_path)


def plot_days_to_nth_review(lifecycle: pd.DataFrame, out_path) -> None:
    """Plot milestone distributions for 3rd/5th/10th review arrival."""
    milestone_cols = [
        ("days_to_3rd_review", "3rd review"),
        ("days_to_5th_review", "5th review"),
        ("days_to_10th_review", "10th review"),
    ]
    fig, ax = plt.subplots(figsize=(9, 5))
    plotted = False
    for column, label in milestone_cols:
        series = lifecycle[column].dropna()
        if series.empty:
            continue
        values = np.sort(series.to_numpy())
        cdf = np.arange(1, len(values) + 1) / len(values)
        ax.plot(values, cdf, label=label)
        plotted = True

    if not plotted:
        logger.warning("No milestone data available for nth-review plot.")
        plt.close(fig)
        return

    ax.set_xlabel("Days Since First Review")
    ax.set_ylabel("CDF")
    ax.set_title("Track D: Days to Early Review Milestones")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 1: Business Lifecycle")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    reviews = load_parquet(
        paths.review_fact_path,
        """
        SELECT review_id, business_id, city, categories, review_date
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    lifecycle = build_business_lifecycle(reviews)
    out = paths.tables_dir / "track_d_s1_business_lifecycle.parquet"
    lifecycle.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(lifecycle))

    plot_review_accrual_curves(reviews, paths.figures_dir / "track_d_s1_review_accrual_curves.png")
    plot_days_to_nth_review(lifecycle, paths.figures_dir / "track_d_s1_days_to_nth_review.png")
    logger.info("Stage 1 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
