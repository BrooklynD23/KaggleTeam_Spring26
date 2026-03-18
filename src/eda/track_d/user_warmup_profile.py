"""Stage 6: D2 warm-up profile and feature coverage."""

from __future__ import annotations

import argparse
import logging
import math

import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import ensure_output_dirs, feature_coverage_frame, load_parquet, primary_category, resolve_paths

logger = logging.getLogger(__name__)


def _entropy(values: pd.Series) -> float | None:
    counts = values.value_counts()
    if counts.empty:
        return None
    probs = counts / counts.sum()
    return float(-(probs * probs.map(math.log2)).sum())


def _join_unique(values: pd.Series) -> str | None:
    uniques = sorted({str(value).strip() for value in values.dropna() if str(value).strip()})
    if not uniques:
        return None
    return "|".join(uniques)


def build_user_warmup_profile(cohort_df: pd.DataFrame, review_df: pd.DataFrame) -> pd.DataFrame:
    """Build as-of aggregate user warm-up features from prior reviews."""
    if cohort_df.empty:
        return pd.DataFrame()

    review_df = review_df.copy()
    review_df["review_date"] = pd.to_datetime(review_df["review_date"])
    review_df["primary_category"] = review_df["categories"].map(primary_category)

    frames: list[pd.DataFrame] = []
    for as_of_date, chunk in cohort_df.groupby("as_of_date", sort=True):
        as_of_ts = pd.Timestamp(as_of_date)
        prior = review_df.loc[review_df["review_date"] < as_of_ts].copy()
        if prior.empty:
            agg = pd.DataFrame(columns=[
                "user_id",
                "prior_categories",
                "prior_cities",
                "prior_avg_stars",
                "prior_review_length_mean",
                "prior_unique_business_count",
                "prior_primary_category_entropy",
            ])
        else:
            agg = (
                prior.groupby("user_id", as_index=False)
                .agg(
                    prior_categories=("primary_category", _join_unique),
                    prior_cities=("city", _join_unique),
                    prior_avg_stars=("review_stars", "mean"),
                    prior_review_length_mean=("text_word_count", "mean"),
                    prior_unique_business_count=("business_id", "nunique"),
                    prior_primary_category_entropy=("primary_category", _entropy),
                )
            )
        merged = chunk.merge(agg, on="user_id", how="left")
        zero_mask = merged["prior_total_interaction_count"].fillna(0).astype(int) == 0
        for column in [
            "prior_categories",
            "prior_cities",
            "prior_avg_stars",
            "prior_review_length_mean",
            "prior_unique_business_count",
            "prior_primary_category_entropy",
        ]:
            merged.loc[zero_mask, column] = pd.NA
        frames.append(merged)

    return pd.concat(frames, ignore_index=True)


def summarize_feature_coverage(warmup_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize D2 warm-up feature coverage by cohort label."""
    summary = feature_coverage_frame(
        warmup_df,
        "cohort_label",
        [
            "prior_categories",
            "prior_cities",
            "prior_avg_stars",
            "prior_review_length_mean",
            "prior_unique_business_count",
            "prior_primary_category_entropy",
        ],
        subtrack="D2",
    )
    if not summary.empty:
        summary = summary.rename(columns={"cohort_label": "segment_label"})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 6: User Warm-Up Profile")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    cohort_df = load_parquet(paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet")
    review_df = load_parquet(
        paths.review_fact_path,
        """
        SELECT user_id, business_id, review_date, review_stars, text_word_count, city, categories
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    warmup_df = build_user_warmup_profile(cohort_df, review_df)
    coverage_df = summarize_feature_coverage(warmup_df)

    warmup_out = paths.tables_dir / "track_d_s6_user_warmup_profile.parquet"
    warmup_df.to_parquet(warmup_out, index=False)
    logger.info("Wrote %s (%d rows)", warmup_out, len(warmup_df))

    coverage_out = paths.tables_dir / "track_d_s6_user_feature_coverage.parquet"
    coverage_df.to_parquet(coverage_out, index=False)
    logger.info("Wrote %s (%d rows)", coverage_out, len(coverage_df))
    logger.info("Stage 6 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
