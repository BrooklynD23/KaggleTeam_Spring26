"""Stage 8: Check-in correlation for Track C."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_c.common import (
    ensure_output_dirs,
    month_label,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def build_checkin_monthly(
    con: duckdb.DuckDBPyConnection,
    checkin_expanded_path: str,
    checkin_path: str,
    business_path: str,
) -> pd.DataFrame:
    """Build city-month check-in volume, falling back to inline parsing."""
    pq_business = str(business_path).replace("\\", "/")
    if Path(checkin_expanded_path).is_file():
        pq_ce = str(checkin_expanded_path).replace("\\", "/")
        sql = f"""
            SELECT
                b.city,
                LOWER(TRIM(b.city)) AS normalized_city,
                b.state,
                EXTRACT(YEAR FROM ce.checkin_date) AS checkin_year,
                EXTRACT(MONTH FROM ce.checkin_date) AS checkin_month,
                COUNT(*) AS checkin_count
            FROM read_parquet('{pq_ce}') ce
            JOIN read_parquet('{pq_business}') b USING (business_id)
            GROUP BY b.city, normalized_city, b.state, checkin_year, checkin_month
        """
        df = con.execute(sql).fetchdf()
    else:
        logger.warning(
            "Missing checkin_expanded.parquet; parsing checkin.parquet inline for Track C."
        )
        pq_checkin = str(checkin_path).replace("\\", "/")
        sql = f"""
            WITH exploded AS (
                SELECT
                    c.business_id,
                    TRY_CAST(TRIM(token.value) AS DATE) AS checkin_date
                FROM read_parquet('{pq_checkin}') c,
                UNNEST(STRING_SPLIT(c.date, ',')) AS token(value)
                WHERE TRIM(token.value) != ''
            )
            SELECT
                b.city,
                LOWER(TRIM(b.city)) AS normalized_city,
                b.state,
                EXTRACT(YEAR FROM e.checkin_date) AS checkin_year,
                EXTRACT(MONTH FROM e.checkin_date) AS checkin_month,
                COUNT(*) AS checkin_count
            FROM exploded e
            JOIN read_parquet('{pq_business}') b USING (business_id)
            WHERE e.checkin_date IS NOT NULL
            GROUP BY b.city, normalized_city, b.state, checkin_year, checkin_month
        """
        df = con.execute(sql).fetchdf()
    if df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "year_month",
                "checkin_count",
            ]
        )
    df["year_month"] = [
        month_label(year, month)
        for year, month in zip(df["checkin_year"], df["checkin_month"], strict=True)
    ]
    return df[["city", "normalized_city", "state", "year_month", "checkin_count"]]


def build_correlation_table(
    monthly_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute contemporaneous and lagged correlations by city."""
    if monthly_df.empty or sentiment_df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "state",
                "paired_months",
                "pearson_corr",
                "spearman_corr",
                "lag1_pearson_corr",
                "lag1_spearman_corr",
            ]
        )
    merged = monthly_df.merge(
        sentiment_df,
        on=["city", "normalized_city", "state", "year_month"],
        how="inner",
    ).sort_values(["city", "year_month"])
    rows: list[dict[str, object]] = []
    for (city, state), frame in merged.groupby(["city", "state"], dropna=False):
        lagged = frame.copy()
        lagged["lag_checkin_count"] = lagged["checkin_count"].shift(1)
        rows.append(
            {
                "city": city,
                "state": state,
                "paired_months": int(len(frame)),
                "pearson_corr": float(frame["checkin_count"].corr(frame["mean_sentiment"], method="pearson"))
                if len(frame) >= 2
                else None,
                "spearman_corr": float(frame["checkin_count"].corr(frame["mean_sentiment"], method="spearman"))
                if len(frame) >= 2
                else None,
                "lag1_pearson_corr": float(
                    lagged["lag_checkin_count"].corr(lagged["mean_sentiment"], method="pearson")
                )
                if lagged["lag_checkin_count"].notna().sum() >= 2
                else None,
                "lag1_spearman_corr": float(
                    lagged["lag_checkin_count"].corr(lagged["mean_sentiment"], method="spearman")
                )
                if lagged["lag_checkin_count"].notna().sum() >= 2
                else None,
            }
        )
    return pd.DataFrame(rows).sort_values("paired_months", ascending=False)


def plot_checkin_vs_sentiment(monthly_df: pd.DataFrame, sentiment_df: pd.DataFrame, output_path: str) -> None:
    """Plot check-ins and sentiment for the strongest-covered city."""
    merged = monthly_df.merge(
        sentiment_df,
        on=["city", "normalized_city", "state", "year_month"],
        how="inner",
    ).sort_values(["city", "year_month"])
    if merged.empty:
        save_placeholder_figure(Path(output_path), "Track C: Check-ins vs Sentiment")
        return
    city = (
        merged.groupby("city")["checkin_count"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )
    city_df = merged.loc[merged["city"] == city].sort_values("year_month")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(city_df["year_month"], city_df["checkin_count"], color="#2563eb", label="checkins")
    ax1.set_ylabel("Check-in Count", color="#2563eb")
    ax1.tick_params(axis="x", rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(city_df["year_month"], city_df["mean_sentiment"], color="#dc2626", label="sentiment")
    ax2.set_ylabel("Mean Sentiment", color="#dc2626")
    ax1.set_title(f"Track C: Check-ins vs Sentiment ({city})")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 8: Check-in Correlation")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    con = connect_duckdb(config)
    try:
        monthly_df = build_checkin_monthly(
            con,
            str(paths.checkin_expanded_path),
            str(paths.checkin_path),
            str(paths.business_path),
        )
    finally:
        con.close()

    sentiment_path = paths.tables_dir / "track_c_s4_sentiment_by_city_month.parquet"
    sentiment_df = pd.read_parquet(sentiment_path) if sentiment_path.is_file() else pd.DataFrame()
    corr_df = build_correlation_table(monthly_df, sentiment_df)

    write_parquet(
        monthly_df,
        paths.tables_dir / "track_c_s8_checkin_volume_monthly.parquet",
    )
    write_parquet(
        corr_df,
        paths.tables_dir / "track_c_s8_checkin_sentiment_correlation.parquet",
    )
    plot_checkin_vs_sentiment(
        monthly_df,
        sentiment_df,
        str(paths.figures_dir / "track_c_s8_checkin_vs_sentiment.png"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
