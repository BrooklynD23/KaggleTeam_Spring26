"""Stage 7: D1 and D2 evaluation cohort construction.

Rewritten to use DuckDB for all heavy joins/aggregations instead of
per-row pandas iteration, reducing runtime from hours to minutes.
"""

from __future__ import annotations

import argparse
import logging
import time
from typing import Any

import duckdb
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_d.common import ensure_output_dirs, load_parquet, load_track_a_splits, resolve_paths

logger = logging.getLogger(__name__)


def _cap_entities_per_group(
    df: pd.DataFrame,
    *,
    entity_col: str,
    group_col: str,
    cap: int,
) -> pd.DataFrame:
    """Keep a deterministic prefix of each cohort group."""
    if cap <= 0 or df.empty:
        return df.copy()
    ranked = df.sort_values([group_col, entity_col]).copy()
    ranked["_cohort_rn"] = ranked.groupby(group_col).cumcount() + 1
    capped = ranked.loc[ranked["_cohort_rn"] <= cap].drop(columns=["_cohort_rn"])
    return capped


def _ordered_unique(values: list[str]) -> list[str]:
    """Return values in input order with duplicates removed."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def exclude_seen_businesses(
    candidates: pd.DataFrame,
    seen_business_ids: set[str] | frozenset[str],
) -> pd.DataFrame:
    """Drop candidate businesses already seen by the user.

    This lightweight helper is kept for regression tests and for any future
    pandas-side filtering before candidate sets are materialized.
    """
    if candidates.empty or "candidate_business_id" not in candidates.columns:
        return candidates.copy()
    if not seen_business_ids:
        return candidates.copy()
    return candidates.loc[
        ~candidates["candidate_business_id"].isin(seen_business_ids)
    ].copy()


def _build_d1_eval_one_date(
    business_cohort_path: str,
    baseline_path: str,
    review_df: pd.DataFrame,
    as_of_date: str,
    end_date: str,
    max_candidate_size: int,
    entity_cap_per_group: int,
) -> pd.DataFrame:
    """Build D1 evaluation for a single as_of_date slice via bounded pandas joins."""
    cohort = pd.read_parquet(
        business_cohort_path,
        columns=["business_id", "city", "primary_category", "cohort_label", "as_of_date"],
    )
    cohort["as_of_date"] = pd.to_datetime(cohort["as_of_date"])
    cohort = cohort.loc[cohort["as_of_date"] == pd.Timestamp(as_of_date)].copy()
    cohort = _cap_entities_per_group(
        cohort,
        entity_col="business_id",
        group_col="cohort_label",
        cap=entity_cap_per_group,
    )

    baseline = pd.read_parquet(
        baseline_path,
        columns=[
            "business_id",
            "city",
            "primary_category",
            "baseline_type",
            "popularity_rank",
            "subtrack",
            "as_of_date",
        ],
    )
    baseline["as_of_date"] = pd.to_datetime(baseline["as_of_date"])
    baseline = baseline.loc[
        (baseline["subtrack"] == "D1")
        & (baseline["as_of_date"] == pd.Timestamp(as_of_date))
        & (baseline["popularity_rank"] <= max_candidate_size)
    ].copy()
    baseline = baseline.sort_values(
        ["baseline_type", "popularity_rank", "business_id"]
    )

    city_to_candidates = (
        baseline.groupby("city", dropna=True)["business_id"].apply(list).to_dict()
    )
    cat_to_candidates = (
        baseline.groupby("primary_category", dropna=True)["business_id"].apply(list).to_dict()
    )

    future_slice = review_df.loc[
        (review_df["review_date"] > pd.Timestamp(as_of_date))
        & (review_df["review_date"] <= pd.Timestamp(end_date))
        & (review_df["business_id"].isin(cohort["business_id"]))
    ]
    labeled_businesses = set(future_slice["business_id"].dropna().astype(str))

    rows: list[dict[str, Any]] = []
    for row in cohort.itertuples(index=False):
        city_candidates = city_to_candidates.get(getattr(row, "city"), [])
        cat_candidates = cat_to_candidates.get(getattr(row, "primary_category"), [])
        candidates = _ordered_unique(
            [str(value) for value in city_candidates + cat_candidates]
        )[:max_candidate_size]
        has_label = str(row.business_id) in labeled_businesses
        for candidate_business_id in candidates:
            rows.append(
                {
                    "subtrack": "D1",
                    "entity_id": row.business_id,
                    "as_of_date": pd.Timestamp(as_of_date),
                    "cohort_label": row.cohort_label,
                    "candidate_set_id": f"D1:{row.business_id}:{as_of_date}",
                    "candidate_business_id": candidate_business_id,
                    "has_label": has_label,
                    "label_business_id": row.business_id if has_label else pd.NA,
                    "was_seen_previously": False,
                    "is_label": has_label and candidate_business_id == row.business_id,
                }
            )
    return pd.DataFrame(rows)


def _build_d1_eval(
    business_cohort_path: str,
    baseline_path: str,
    review_df: pd.DataFrame,
    t1: str,
    t2: str,
    max_review_date: str,
    max_candidate_size: int,
    entity_cap_per_group: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build D1 evaluation cohorts, one as_of_date at a time."""
    end_dates = {t1: t2, t2: max_review_date}
    frames: list[pd.DataFrame] = []
    for aod, ed in end_dates.items():
        t0 = time.perf_counter()
        chunk = _build_d1_eval_one_date(
            business_cohort_path, baseline_path, review_df,
            aod, ed, max_candidate_size, entity_cap_per_group,
        )
        logger.info("D1 eval as_of=%s: %.1f s, %d rows", aod, time.perf_counter() - t0, len(chunk))
        frames.append(chunk)

    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    eval_df = (
        raw.groupby(
            ["subtrack", "entity_id", "as_of_date", "cohort_label",
             "candidate_set_id", "has_label", "label_business_id"],
            as_index=False, dropna=False,
        )
        .agg(candidate_set_size=("candidate_business_id", "count"))
    )
    members_df = raw[[
        "subtrack", "entity_id", "as_of_date", "candidate_set_id",
        "candidate_business_id", "is_label", "was_seen_previously",
    ]].copy()
    return eval_df, members_df


def _build_d2_eval_one_date(
    user_cohort_path: str,
    warmup_path: str,
    baseline_path: str,
    review_df: pd.DataFrame,
    as_of_date: str,
    end_date: str,
    max_candidate_size: int,
    entity_cap_per_group: int,
) -> pd.DataFrame:
    """Build D2 evaluation for a single as_of_date slice via bounded pandas joins."""
    cohort = pd.read_parquet(
        user_cohort_path,
        columns=["user_id", "cohort_label", "is_primary_cohort", "as_of_date"],
    )
    cohort["as_of_date"] = pd.to_datetime(cohort["as_of_date"])
    cohort = cohort.loc[
        (cohort["as_of_date"] == pd.Timestamp(as_of_date))
        & (cohort["is_primary_cohort"].fillna(False))
    ].copy()
    cohort = _cap_entities_per_group(
        cohort,
        entity_col="user_id",
        group_col="cohort_label",
        cap=entity_cap_per_group,
    )

    warmup = pd.read_parquet(
        warmup_path,
        columns=["user_id", "as_of_date", "prior_cities", "prior_categories"],
    )
    warmup["as_of_date"] = pd.to_datetime(warmup["as_of_date"])
    warmup = warmup.loc[warmup["as_of_date"] == pd.Timestamp(as_of_date)].copy()
    warmup = warmup[["user_id", "prior_cities", "prior_categories"]]

    baseline = pd.read_parquet(
        baseline_path,
        columns=[
            "business_id",
            "city",
            "primary_category",
            "baseline_type",
            "popularity_rank",
            "subtrack",
            "as_of_date",
        ],
    )
    baseline["as_of_date"] = pd.to_datetime(baseline["as_of_date"])
    baseline = baseline.loc[
        (baseline["subtrack"] == "D2")
        & (baseline["as_of_date"] == pd.Timestamp(as_of_date))
        & (baseline["popularity_rank"] <= max_candidate_size)
    ].copy()
    baseline = baseline.sort_values(
        ["baseline_type", "popularity_rank", "business_id"]
    )

    city_to_candidates = (
        baseline.groupby("city", dropna=True)["business_id"].apply(list).to_dict()
    )
    cat_to_candidates = (
        baseline.groupby("primary_category", dropna=True)["business_id"].apply(list).to_dict()
    )
    global_candidates = _ordered_unique(
        [str(value) for value in baseline["business_id"].tolist()]
    )[:max_candidate_size]

    cohort = cohort.merge(warmup, on="user_id", how="left")

    future_slice = review_df.loc[
        (review_df["review_date"] > pd.Timestamp(as_of_date))
        & (review_df["review_date"] <= pd.Timestamp(end_date))
        & (review_df["user_id"].isin(cohort["user_id"]))
    ].sort_values(["user_id", "review_date"])
    future_map = (
        future_slice.drop_duplicates("user_id")
        .set_index("user_id")["business_id"]
        .astype(str)
        .to_dict()
    )

    prior_slice = review_df.loc[
        (review_df["review_date"] < pd.Timestamp(as_of_date))
        & (review_df["user_id"].isin(cohort["user_id"]))
    ][["user_id", "business_id"]].dropna()
    seen_map = (
        prior_slice.groupby("user_id")["business_id"]
        .agg(lambda values: set(map(str, values)))
        .to_dict()
    )

    rows: list[dict[str, Any]] = []
    for row in cohort.itertuples(index=False):
        prior_cities = []
        if pd.notna(getattr(row, "prior_cities", pd.NA)):
            prior_cities = [
                token.strip()
                for token in str(row.prior_cities).split("|")
                if token.strip()
            ]
        prior_categories = []
        if pd.notna(getattr(row, "prior_categories", pd.NA)):
            prior_categories = [
                token.strip()
                for token in str(row.prior_categories).split("|")
                if token.strip()
            ]

        if not prior_cities and not prior_categories:
            candidates = list(global_candidates)
        else:
            candidate_values: list[str] = []
            for city in prior_cities:
                candidate_values.extend(
                    [str(value) for value in city_to_candidates.get(city, [])]
                )
            for category in prior_categories:
                candidate_values.extend(
                    [str(value) for value in cat_to_candidates.get(category, [])]
                )
            candidates = _ordered_unique(candidate_values)

        seen_businesses = seen_map.get(row.user_id, set())
        filtered_candidates = [
            candidate for candidate in candidates
            if candidate not in seen_businesses
        ][:max_candidate_size]

        label_business_id = future_map.get(row.user_id)
        has_label = label_business_id is not None
        for candidate_business_id in filtered_candidates:
            rows.append(
                {
                    "subtrack": "D2",
                    "entity_id": row.user_id,
                    "as_of_date": pd.Timestamp(as_of_date),
                    "cohort_label": row.cohort_label,
                    "candidate_set_id": f"D2:{row.user_id}:{as_of_date}",
                    "candidate_business_id": candidate_business_id,
                    "has_label": has_label,
                    "label_business_id": label_business_id if has_label else pd.NA,
                    "was_seen_previously": False,
                    "is_label": has_label and candidate_business_id == label_business_id,
                }
            )
    return pd.DataFrame(rows)


def _build_d2_eval(
    user_cohort_path: str,
    warmup_path: str,
    baseline_path: str,
    review_df: pd.DataFrame,
    t1: str,
    t2: str,
    max_review_date: str,
    max_candidate_size: int,
    entity_cap_per_group: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build D2 evaluation cohorts, one as_of_date at a time."""
    end_dates = {t1: t2, t2: max_review_date}
    frames: list[pd.DataFrame] = []
    for aod, ed in end_dates.items():
        t0 = time.perf_counter()
        chunk = _build_d2_eval_one_date(
            user_cohort_path, warmup_path, baseline_path, review_df,
            aod, ed, max_candidate_size, entity_cap_per_group,
        )
        logger.info("D2 eval as_of=%s: %.1f s, %d rows", aod, time.perf_counter() - t0, len(chunk))
        frames.append(chunk)

    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    eval_df = (
        raw.groupby(
            ["subtrack", "entity_id", "as_of_date", "cohort_label",
             "candidate_set_id", "has_label", "label_business_id"],
            as_index=False, dropna=False,
        )
        .agg(candidate_set_size=("candidate_business_id", "count"))
    )
    members_df = raw[[
        "subtrack", "entity_id", "as_of_date", "candidate_set_id",
        "candidate_business_id", "is_label", "was_seen_previously",
    ]].copy()
    return eval_df, members_df


def summarize_eval_cohorts(eval_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate evaluation cohort summary statistics."""
    if eval_df.empty:
        return pd.DataFrame(columns=[
            "subtrack", "as_of_date", "cohort_label",
            "entity_count", "label_rate", "avg_candidate_set_size",
        ])
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

    rf_pq = str(paths.review_fact_path).replace("\\", "/")
    biz_cohort_pq = str(paths.tables_dir / "track_d_s2_business_cold_start_cohort.parquet").replace("\\", "/")
    baseline_pq = str(paths.tables_dir / "track_d_s4_popularity_baseline_asof.parquet").replace("\\", "/")
    user_cohort_pq = str(paths.tables_dir / "track_d_s5_user_cold_start_cohort.parquet").replace("\\", "/")
    warmup_pq = str(paths.tables_dir / "track_d_s6_user_warmup_profile.parquet").replace("\\", "/")

    t1, t2, _ = load_track_a_splits(config, paths.tables_dir)

    con = connect_duckdb(config)
    try:
        max_review_date = con.execute(
            f"SELECT MAX(review_date)::VARCHAR FROM read_parquet('{rf_pq}') WHERE review_date IS NOT NULL"
        ).fetchone()[0]  # type: ignore[index]

        max_candidate_size = int(config["baseline"]["candidate_set_max_size"])
        entity_cap_per_group = int(
            config.get("evaluation", {}).get("entity_cap_per_group", 10_000)
        )
        logger.info(
            "Stage 7 evaluation cap: max_candidate_size=%d entity_cap_per_group=%d",
            max_candidate_size,
            entity_cap_per_group,
        )
        review_df = load_parquet(
            paths.review_fact_path,
            """
            SELECT user_id, business_id, review_date
            FROM read_parquet(?)
            WHERE review_date IS NOT NULL
            """,
            [str(paths.review_fact_path)],
        )
        review_df["review_date"] = pd.to_datetime(review_df["review_date"])

        d1_eval_df, d1_members_df = _build_d1_eval(
            biz_cohort_pq,
            baseline_pq,
            review_df,
            t1,
            t2,
            max_review_date,
            max_candidate_size,
            entity_cap_per_group,
        )
        d2_eval_df, d2_members_df = _build_d2_eval(
            user_cohort_pq,
            warmup_pq,
            baseline_pq,
            review_df,
            t1,
            t2,
            max_review_date,
            max_candidate_size,
            entity_cap_per_group,
        )
    finally:
        con.close()

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
