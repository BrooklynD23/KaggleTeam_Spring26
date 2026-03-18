"""Stage 7: D1 and D2 evaluation cohort construction."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import load_config
from src.eda.track_d.common import ensure_output_dirs, load_parquet, load_track_a_splits, resolve_paths

logger = logging.getLogger(__name__)


def exclude_seen_businesses(candidate_df: pd.DataFrame, seen_business_ids: set[str]) -> pd.DataFrame:
    """Remove businesses already seen before the evaluation point."""
    if candidate_df.empty or not seen_business_ids:
        return candidate_df.copy()
    return candidate_df.loc[~candidate_df["candidate_business_id"].isin(seen_business_ids)].reset_index(drop=True)


def _next_review_after(review_df: pd.DataFrame, entity_col: str, as_of_date: pd.Timestamp, entity_id: str, end_date: pd.Timestamp | None) -> pd.DataFrame:
    mask = (review_df[entity_col] == entity_id) & (review_df["review_date"] > as_of_date)
    if end_date is not None:
        mask &= review_df["review_date"] <= end_date
    return review_df.loc[mask].sort_values(["review_date", "review_id"])


def _candidate_set_id(subtrack: str, entity_id: str, as_of_date: pd.Timestamp) -> str:
    return f"{subtrack}:{entity_id}:{as_of_date.date().isoformat()}"


def _build_d1_eval(
    business_cohort_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    review_df: pd.DataFrame,
    end_dates: dict[pd.Timestamp, pd.Timestamp | None],
    max_candidate_size: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    eval_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []

    d1_baseline = baseline_df.loc[baseline_df["subtrack"] == "D1"].copy()
    for row in business_cohort_df.itertuples(index=False):
        as_of_date = pd.Timestamp(row.as_of_date)
        end_date = end_dates.get(as_of_date)
        future_reviews = _next_review_after(review_df, "business_id", as_of_date, row.business_id, end_date)
        has_label = not future_reviews.empty

        pool = d1_baseline.loc[
            (pd.to_datetime(d1_baseline["as_of_date"]) == as_of_date)
            & (
                (d1_baseline["city"] == getattr(row, "city", None))
                | (d1_baseline["primary_category"] == getattr(row, "primary_category", None))
            )
        ].copy()
        pool = pool.sort_values(["baseline_type", "popularity_rank", "business_id"]).drop_duplicates("business_id")
        pool = pool.head(max_candidate_size)

        if has_label and row.business_id not in set(pool["business_id"].tolist()):
            label_meta = {
                "business_id": row.business_id,
                "city": getattr(row, "city", None),
                "primary_category": getattr(row, "primary_category", None),
                "baseline_type": "held_out_label",
                "popularity_rank": len(pool) + 1,
            }
            pool = pd.concat([pool, pd.DataFrame([label_meta])], ignore_index=True)

        candidate_set_id = _candidate_set_id("D1", row.business_id, as_of_date)
        eval_rows.append(
            {
                "subtrack": "D1",
                "entity_id": row.business_id,
                "as_of_date": as_of_date,
                "cohort_label": row.cohort_label,
                "candidate_set_id": candidate_set_id,
                "candidate_set_size": len(pool),
                "has_label": has_label,
                "label_business_id": row.business_id if has_label else pd.NA,
            }
        )
        for candidate in pool.itertuples(index=False):
            member_rows.append(
                {
                    "subtrack": "D1",
                    "entity_id": row.business_id,
                    "as_of_date": as_of_date,
                    "candidate_set_id": candidate_set_id,
                    "candidate_business_id": candidate.business_id,
                    "is_label": bool(has_label and candidate.business_id == row.business_id),
                    "was_seen_previously": False,
                }
            )

    return pd.DataFrame(eval_rows), pd.DataFrame(member_rows)


def _build_d2_eval(
    user_cohort_df: pd.DataFrame,
    warmup_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    review_df: pd.DataFrame,
    end_dates: dict[pd.Timestamp, pd.Timestamp | None],
    max_candidate_size: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    eval_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    d2_baseline = baseline_df.loc[baseline_df["subtrack"] == "D2"].copy()

    warmup_lookup = warmup_df.set_index(["user_id", "as_of_date"]) if not warmup_df.empty else None
    for row in user_cohort_df.itertuples(index=False):
        as_of_date = pd.Timestamp(row.as_of_date)
        end_date = end_dates.get(as_of_date)
        future_reviews = _next_review_after(review_df, "user_id", as_of_date, row.user_id, end_date)
        label_business_id = future_reviews.iloc[0]["business_id"] if not future_reviews.empty else pd.NA
        seen_business_ids = set(
            review_df.loc[
                (review_df["user_id"] == row.user_id) & (review_df["review_date"] < as_of_date),
                "business_id",
            ].dropna()
        )

        prior_cities: set[str] = set()
        prior_categories: set[str] = set()
        if warmup_lookup is not None and (row.user_id, row.as_of_date) in warmup_lookup.index:
            warm = warmup_lookup.loc[(row.user_id, row.as_of_date)]
            if isinstance(warm, pd.DataFrame):
                warm = warm.iloc[0]
            cities_value = warm.get("prior_cities")
            categories_value = warm.get("prior_categories")
            if pd.notna(cities_value):
                prior_cities = {part for part in str(cities_value).split("|") if part}
            if pd.notna(categories_value):
                prior_categories = {part for part in str(categories_value).split("|") if part}

        pool = d2_baseline.loc[pd.to_datetime(d2_baseline["as_of_date"]) == as_of_date].copy()
        if prior_cities or prior_categories:
            pool = pool.loc[
                pool["city"].isin(prior_cities) | pool["primary_category"].isin(prior_categories)
            ]
        pool = pool.sort_values(["baseline_type", "popularity_rank", "business_id"]).drop_duplicates("business_id")
        pool = pool.rename(columns={"business_id": "candidate_business_id"})
        pool["was_seen_previously"] = pool["candidate_business_id"].isin(seen_business_ids)
        pool = exclude_seen_businesses(pool, seen_business_ids).head(max_candidate_size)

        if pd.notna(label_business_id) and label_business_id not in set(pool["candidate_business_id"].tolist()):
            if label_business_id not in seen_business_ids:
                pool = pd.concat(
                    [
                        pool,
                        pd.DataFrame(
                            [
                                {
                                    "candidate_business_id": label_business_id,
                                    "was_seen_previously": False,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

        candidate_set_id = _candidate_set_id("D2", row.user_id, as_of_date)
        has_label = pd.notna(label_business_id) and label_business_id in set(pool["candidate_business_id"].tolist())
        eval_rows.append(
            {
                "subtrack": "D2",
                "entity_id": row.user_id,
                "as_of_date": as_of_date,
                "cohort_label": row.cohort_label,
                "candidate_set_id": candidate_set_id,
                "candidate_set_size": len(pool),
                "has_label": bool(has_label),
                "label_business_id": label_business_id if has_label else pd.NA,
            }
        )
        for candidate in pool.itertuples(index=False):
            member_rows.append(
                {
                    "subtrack": "D2",
                    "entity_id": row.user_id,
                    "as_of_date": as_of_date,
                    "candidate_set_id": candidate_set_id,
                    "candidate_business_id": candidate.candidate_business_id,
                    "is_label": bool(has_label and candidate.candidate_business_id == label_business_id),
                    "was_seen_previously": bool(getattr(candidate, "was_seen_previously", False)),
                }
            )

    return pd.DataFrame(eval_rows), pd.DataFrame(member_rows)


def summarize_eval_cohorts(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate evaluation cohort counts by subtrack and label."""
    if eval_df.empty:
        return pd.DataFrame(columns=["subtrack", "as_of_date", "cohort_label", "entity_count", "label_rate", "avg_candidate_set_size"])
    return (
        eval_df.groupby(["subtrack", "as_of_date", "cohort_label"], as_index=False)
        .agg(
            entity_count=("entity_id", "count"),
            label_rate=("has_label", "mean"),
            avg_candidate_set_size=("candidate_set_size", "mean"),
        )
        .sort_values(["subtrack", "as_of_date", "cohort_label"])
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 7: Evaluation Cohorts")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    business_cohort_df = load_parquet(paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet")
    baseline_df = load_parquet(paths.tables_dir / "track_d_s4_popularity_baseline_asof.parquet")
    user_cohort_df = load_parquet(paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet")
    warmup_df = load_parquet(paths.tables_dir / "track_d_s6_user_warmup_profile.parquet")
    review_df = load_parquet(
        paths.review_fact_path,
        """
        SELECT review_id, user_id, business_id, review_date
        FROM read_parquet(?)
        WHERE review_date IS NOT NULL
        """,
        [str(paths.review_fact_path)],
    )
    review_df["review_date"] = pd.to_datetime(review_df["review_date"])

    t1, t2, _ = load_track_a_splits(config, paths.tables_dir)
    max_review_date = review_df["review_date"].max() if not review_df.empty else None
    end_dates = {
        pd.Timestamp(t1): pd.Timestamp(t2),
        pd.Timestamp(t2): pd.Timestamp(max_review_date) if max_review_date is not None else None,
    }

    max_candidate_size = int(config["baseline"]["candidate_set_max_size"])
    d1_eval_df, d1_members_df = _build_d1_eval(
        business_cohort_df,
        baseline_df,
        review_df,
        end_dates,
        max_candidate_size,
    )
    d2_eval_df, d2_members_df = _build_d2_eval(
        user_cohort_df,
        warmup_df,
        baseline_df,
        review_df,
        end_dates,
        max_candidate_size,
    )

    eval_df = pd.concat([d1_eval_df, d2_eval_df], ignore_index=True)
    members_df = pd.concat([d1_members_df, d2_members_df], ignore_index=True)
    summary_df = summarize_eval_cohorts(eval_df)

    eval_out = paths.tables_dir / "track_d_s7_eval_cohorts.parquet"
    eval_df.to_parquet(eval_out, index=False)
    logger.info("Wrote %s (%d rows)", eval_out, len(eval_df))

    summary_out = paths.tables_dir / "track_d_s7_eval_cohort_summary.parquet"
    summary_df.to_parquet(summary_out, index=False)
    logger.info("Wrote %s (%d rows)", summary_out, len(summary_df))

    members_out = paths.tables_dir / "track_d_s7_eval_candidate_members.parquet"
    members_df.to_parquet(members_out, index=False)
    logger.info("Wrote %s (%d rows)", members_out, len(members_df))
    logger.info("Stage 7 complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
