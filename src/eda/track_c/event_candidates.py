"""Stage 7: Event candidate profiling for Track C."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.eda.track_c.common import (
    ensure_output_dirs,
    load_snapshot_metadata,
    primary_category,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def build_business_lifecycle(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: str,
    business_path: str,
    snapshot_reference_date: str,
    inactivity_days: int,
) -> pd.DataFrame:
    """Build business lifecycle and closure-candidate summaries."""
    lifecycle = con.execute(
        """
        WITH review_lifecycle AS (
            SELECT
                business_id,
                MIN(review_date) AS first_review_date,
                MAX(review_date) AS last_review_date,
                COUNT(*) AS review_count
            FROM read_parquet($1)
            GROUP BY business_id
        )
        SELECT
            rl.business_id,
            b.city,
            b.state,
            b.categories,
            b.is_open,
            rl.first_review_date::VARCHAR AS first_review_date,
            rl.last_review_date::VARCHAR AS last_review_date,
            rl.review_count
        FROM review_lifecycle rl
        JOIN read_parquet($2) b USING (business_id)
        """,
        [review_fact_path, business_path],
    ).fetchdf()
    if lifecycle.empty:
        return pd.DataFrame(
            columns=[
                "business_id",
                "city",
                "state",
                "primary_category",
                "is_open",
                "first_review_date",
                "last_review_date",
                "review_count",
                "days_since_last_review",
                "closure_candidate",
                "opening_proxy_date",
            ]
        )
    lifecycle["primary_category"] = lifecycle["categories"].apply(primary_category)
    lifecycle = lifecycle.drop(columns=["categories"])
    lifecycle["first_review_date"] = pd.to_datetime(lifecycle["first_review_date"])
    lifecycle["last_review_date"] = pd.to_datetime(lifecycle["last_review_date"])
    snapshot_date = pd.to_datetime(snapshot_reference_date)
    lifecycle["days_since_last_review"] = (
        snapshot_date - lifecycle["last_review_date"]
    ).dt.days
    lifecycle["closure_candidate"] = (
        lifecycle["is_open"].fillna(1).astype(int).eq(0)
        & lifecycle["days_since_last_review"].ge(inactivity_days)
    )
    lifecycle["opening_proxy_date"] = lifecycle["first_review_date"]
    lifecycle["first_review_date"] = lifecycle["first_review_date"].dt.date.astype(str)
    lifecycle["last_review_date"] = lifecycle["last_review_date"].dt.date.astype(str)
    lifecycle["opening_proxy_date"] = pd.to_datetime(lifecycle["opening_proxy_date"]).dt.date.astype(str)
    return lifecycle


def build_event_candidates(
    lifecycle_df: pd.DataFrame,
    sentiment_drift_df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate event-candidate counts by city and join drift flags."""
    if lifecycle_df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "state",
                "opening_count",
                "closure_candidate_count",
                "mean_days_since_last_review",
                "drift_significant_count",
            ]
        )
    summary = (
        lifecycle_df.groupby(["city", "state"], dropna=False, as_index=False)
        .agg(
            opening_count=("opening_proxy_date", "count"),
            closure_candidate_count=("closure_candidate", "sum"),
            mean_days_since_last_review=("days_since_last_review", "mean"),
        )
    )
    if not sentiment_drift_df.empty:
        drift_summary = (
            sentiment_drift_df.groupby(["city", "state"], dropna=False, as_index=False)
            .agg(drift_significant_count=("is_significant", "sum"))
        )
        summary = summary.merge(drift_summary, on=["city", "state"], how="left")
    else:
        summary["drift_significant_count"] = 0
    summary["drift_significant_count"] = summary["drift_significant_count"].fillna(0).astype(int)
    return summary.sort_values(
        ["closure_candidate_count", "opening_count"],
        ascending=[False, False],
    )


def plot_lifecycle_timeline(lifecycle_df: pd.DataFrame, output_path: str) -> None:
    """Plot monthly openings and closure candidates."""
    if lifecycle_df.empty:
        save_placeholder_figure(Path(output_path), "Track C: Open/Close Timeline")
        return
    openings = (
        pd.to_datetime(lifecycle_df["opening_proxy_date"])
        .dt.to_period("M")
        .astype(str)
        .value_counts()
        .sort_index()
    )
    closures = (
        pd.to_datetime(lifecycle_df.loc[lifecycle_df["closure_candidate"], "last_review_date"])
        .dt.to_period("M")
        .astype(str)
        .value_counts()
        .sort_index()
    )
    timeline = pd.DataFrame({"openings": openings, "closures": closures}).fillna(0)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(timeline.index, timeline["openings"], label="openings", color="#16a34a")
    ax.plot(timeline.index, timeline["closures"], label="closure candidates", color="#dc2626")
    ax.set_title("Track C: Business Lifecycle Timeline")
    ax.set_ylabel("Businesses")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 7: Event Candidates")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    metadata = load_snapshot_metadata(paths)
    snapshot_reference_date = metadata.get("snapshot_reference_date", "2022-01-19")
    inactivity_days = int(
        config.get("events", {}).get("inactivity_close_proxy_days", 180)
    )

    con = duckdb.connect()
    try:
        lifecycle_df = build_business_lifecycle(
            con,
            str(paths.review_fact_path),
            str(paths.business_path),
            snapshot_reference_date,
            inactivity_days,
        )
    finally:
        con.close()

    sentiment_drift_path = paths.tables_dir / "track_c_s6_sentiment_drift_by_city.parquet"
    sentiment_drift_df = (
        pd.read_parquet(sentiment_drift_path) if sentiment_drift_path.is_file() else pd.DataFrame()
    )
    event_df = build_event_candidates(lifecycle_df, sentiment_drift_df)

    write_parquet(
        lifecycle_df,
        paths.tables_dir / "track_c_s7_business_lifecycle.parquet",
    )
    write_parquet(event_df, paths.tables_dir / "track_c_s7_event_candidates.parquet")
    plot_lifecycle_timeline(
        lifecycle_df,
        str(paths.figures_dir / "track_c_s7_open_close_timeline.png"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
