"""Stage 3: D1 business early-signal catalog."""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import (
    count_attributes,
    ensure_output_dirs,
    extract_price_range,
    feature_coverage_frame,
    load_checkins,
    load_parquet,
    primary_category,
    resolve_paths,
)

logger = logging.getLogger(__name__)

INTERACTION_FEATURES = [
    "prior_review_mean_stars",
    "prior_review_mean_length",
    "prior_tip_count",
    "prior_checkin_count",
]


def _build_history_lookup(frame: pd.DataFrame, entity_col: str, date_col: str, value_map: dict[str, str]) -> list[pd.DataFrame]:
    """Placeholder to make intent explicit for stage-local aggregation."""
    if frame.empty:
        return []
    converted = frame.copy()
    converted[date_col] = pd.to_datetime(converted[date_col])
    return [converted]


def build_business_early_signals(
    cohort_df: pd.DataFrame,
    business_df: pd.DataFrame,
    review_df: pd.DataFrame,
    tip_df: pd.DataFrame,
    checkin_df: pd.DataFrame,
) -> pd.DataFrame:
    """Build Track D1 business features available at each as-of date."""
    if cohort_df.empty:
        return pd.DataFrame()

    business = business_df.copy()
    business["primary_category"] = business["categories"].map(primary_category)
    business["price_range"] = business["attributes"].map(extract_price_range)
    business["has_hours"] = business["hours"].notna()
    business["attribute_count"] = business["attributes"].map(count_attributes)
    static_cols = [
        "business_id",
        "city",
        "state",
        "categories",
        "primary_category",
        "price_range",
        "has_hours",
        "attribute_count",
        "latitude",
        "longitude",
    ]
    base = cohort_df.merge(business[static_cols], on=["business_id", "city", "state", "categories", "primary_category"], how="left")

    review_df = review_df.copy()
    review_df["review_date"] = pd.to_datetime(review_df["review_date"])
    tip_df = tip_df.copy()
    if not tip_df.empty:
        tip_df["tip_date"] = pd.to_datetime(tip_df["tip_date"])
    checkin_df = checkin_df.copy()
    if not checkin_df.empty:
        checkin_df["checkin_date"] = pd.to_datetime(checkin_df["checkin_date"])

    enriched_frames: list[pd.DataFrame] = []
    for as_of_date, cohort_chunk in base.groupby("as_of_date", sort=True):
        as_of_ts = pd.Timestamp(as_of_date)
        review_prior = (
            review_df.loc[review_df["review_date"] < as_of_ts]
            .groupby("business_id", as_index=False)
            .agg(
                prior_review_mean_stars=("review_stars", "mean"),
                prior_review_mean_length=("text_word_count", "mean"),
            )
        )
        tip_prior = (
            tip_df.loc[tip_df["tip_date"] < as_of_ts].groupby("business_id", as_index=False).size().rename(columns={"size": "prior_tip_count"})
            if not tip_df.empty
            else pd.DataFrame(columns=["business_id", "prior_tip_count"])
        )
        checkin_prior = (
            checkin_df.loc[checkin_df["checkin_date"] < as_of_ts]
            .groupby("business_id", as_index=False)
            .size()
            .rename(columns={"size": "prior_checkin_count"})
            if not checkin_df.empty
            else pd.DataFrame(columns=["business_id", "prior_checkin_count"])
        )

        chunk = cohort_chunk.merge(review_prior, on="business_id", how="left")
        chunk = chunk.merge(tip_prior, on="business_id", how="left")
        chunk = chunk.merge(checkin_prior, on="business_id", how="left")
        chunk["prior_tip_count"] = chunk["prior_tip_count"].fillna(0)
        chunk["prior_checkin_count"] = chunk["prior_checkin_count"].fillna(0)

        zero_mask = chunk["prior_review_count"].fillna(0).astype(int) == 0
        for column in INTERACTION_FEATURES:
            chunk.loc[zero_mask, column] = pd.NA
        enriched_frames.append(chunk)

    return pd.concat(enriched_frames, ignore_index=True)


def summarize_signals(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Report feature coverage by D1 cohort label."""
    summary = feature_coverage_frame(
        signals_df,
        "cohort_label",
        [
            "price_range",
            "has_hours",
            "attribute_count",
            "latitude",
            "longitude",
            *INTERACTION_FEATURES,
        ],
        subtrack="D1",
    )
    if not summary.empty:
        summary = summary.rename(columns={"cohort_label": "segment_label"})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 3: Business Early Signals")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    cohort_df = load_parquet(paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet")
    business_df = load_parquet(
        paths.business_path,
        """
        SELECT business_id, city, state, categories, attributes, hours, latitude, longitude
        FROM read_parquet(?)
        """,
        [str(paths.business_path)],
    )
    review_df = load_parquet(
        paths.review_fact_path,
        """
        SELECT business_id, review_date, review_stars, text_word_count
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    tip_df = (
        load_parquet(paths.tip_path, "SELECT business_id, tip_date FROM read_parquet(?) WHERE tip_date IS NOT NULL", [str(paths.tip_path)])
        if paths.tip_path.is_file()
        else pd.DataFrame(columns=["business_id", "tip_date"])
    )
    checkin_df = load_checkins(paths)

    signals_df = build_business_early_signals(cohort_df, business_df, review_df, tip_df, checkin_df)
    summary_df = summarize_signals(signals_df)

    signals_out = paths.tables_dir / "track_d_s3_business_early_signals.parquet"
    signals_df.to_parquet(signals_out, index=False)
    logger.info("Wrote %s (%d rows)", signals_out, len(signals_df))

    summary_out = paths.tables_dir / "track_d_s3_business_signal_summary.parquet"
    summary_df.to_parquet(summary_out, index=False)
    logger.info("Wrote %s (%d rows)", summary_out, len(summary_df))
    logger.info("Stage 3 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
