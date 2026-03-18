"""Stage 4: As-of popularity baselines for D1 and D2."""

from __future__ import annotations

import argparse
import logging

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import ensure_output_dirs, load_parquet, load_track_a_splits, primary_category, resolve_paths

logger = logging.getLogger(__name__)


def _rank_within(frame: pd.DataFrame, group_cols: list[str], sort_cols: list[str], ascending: list[bool]) -> pd.DataFrame:
    ranked = frame.sort_values(group_cols + sort_cols, ascending=[True] * len(group_cols) + ascending).copy()
    ranked["popularity_rank"] = ranked.groupby(group_cols).cumcount() + 1
    return ranked


def build_popularity_baseline(
    review_df: pd.DataFrame,
    business_df: pd.DataFrame,
    as_of_dates: list[str],
    min_support_reviews: int,
) -> pd.DataFrame:
    """Build baseline rankings using only history available before each as-of date."""
    review_df = review_df.copy()
    review_df["review_date"] = pd.to_datetime(review_df["review_date"])
    business_meta = business_df.copy()
    business_meta["primary_category"] = business_meta["categories"].map(primary_category)

    frames: list[pd.DataFrame] = []
    for as_of_value in as_of_dates:
        as_of_date = pd.Timestamp(as_of_value)
        prior = review_df.loc[review_df["review_date"] < as_of_date]
        summary = (
            prior.groupby("business_id", as_index=False)
            .agg(
                prior_review_count=("review_id", "count"),
                prior_avg_stars=("review_stars", "mean"),
            )
        )
        enriched = summary.merge(
            business_meta[["business_id", "city", "state", "primary_category"]],
            on="business_id",
            how="left",
        )
        enriched["as_of_date"] = as_of_date.normalize()

        by_city = _rank_within(
            enriched.copy(),
            ["city"],
            ["prior_review_count", "prior_avg_stars", "business_id"],
            [False, False, True],
        )
        by_city["baseline_type"] = "most_reviewed_in_city"

        rated_city = enriched.loc[enriched["prior_review_count"] >= min_support_reviews].copy()
        rated_city = _rank_within(
            rated_city,
            ["city"],
            ["prior_avg_stars", "prior_review_count", "business_id"],
            [False, False, True],
        )
        rated_city["baseline_type"] = "highest_rated_in_city"

        by_category = _rank_within(
            enriched.loc[enriched["primary_category"].notna()].copy(),
            ["primary_category"],
            ["prior_review_count", "prior_avg_stars", "business_id"],
            [False, False, True],
        )
        by_category["baseline_type"] = "most_reviewed_in_category"

        combined = pd.concat([by_city, rated_city, by_category], ignore_index=True)
        combined["scope_key"] = combined["city"].fillna(combined["primary_category"])
        for subtrack in ("D1", "D2"):
            tagged = combined.copy()
            tagged["subtrack"] = subtrack
            frames.append(tagged)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def plot_popularity_concentration(baseline_df: pd.DataFrame, out_path) -> None:
    """Plot the share of review history held by top-ranked city businesses."""
    focus = baseline_df.loc[
        (baseline_df["baseline_type"] == "most_reviewed_in_city")
        & (baseline_df["subtrack"] == "D1")
        & (baseline_df["popularity_rank"] <= 10)
    ].copy()
    if focus.empty:
        logger.warning("No baseline rows available for popularity concentration plot.")
        return
    top_share = (
        focus.groupby(["as_of_date", "city"], as_index=False)
        .agg(top10_review_count=("prior_review_count", "sum"))
        .sort_values(["as_of_date", "top10_review_count"], ascending=[True, False])
        .groupby("as_of_date", as_index=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    for as_of_date, chunk in top_share.groupby("as_of_date", sort=True):
        ax.plot(chunk["city"], chunk["top10_review_count"], marker="o", label=str(pd.Timestamp(as_of_date).date()))
    ax.set_xlabel("City")
    ax.set_ylabel("Top-10 Review Count")
    ax.set_title("Track D: Popularity Concentration by City")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="As-of date")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 4: Popularity Baseline")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    reviews = load_parquet(
        paths.review_fact_path,
        """
        SELECT review_id, business_id, review_date, review_stars
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    business_df = load_parquet(
        paths.business_path,
        """
        SELECT business_id, city, state, categories
        FROM read_parquet(?)
        """,
        [str(paths.business_path)],
    )
    t1, t2, _ = load_track_a_splits(config, paths.tables_dir)
    baseline_df = build_popularity_baseline(
        reviews,
        business_df,
        [t1, t2],
        int(config["baseline"]["min_support_reviews"]),
    )
    baseline_out = paths.tables_dir / "track_d_s4_popularity_baseline_asof.parquet"
    baseline_df.to_parquet(baseline_out, index=False)
    logger.info("Wrote %s (%d rows)", baseline_out, len(baseline_df))

    plot_popularity_concentration(baseline_df, paths.figures_dir / "track_d_s4_popularity_concentration.png")
    logger.info("Stage 4 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
