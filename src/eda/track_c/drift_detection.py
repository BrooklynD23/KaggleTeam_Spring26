"""Stage 6: Drift detection for Track C."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import linregress

from src.common.config import load_config
from src.eda.track_c.common import (
    ensure_output_dirs,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _regress(frame: pd.DataFrame, value_column: str) -> dict[str, object]:
    """Compute a simple linear trend summary for a time series frame."""
    if len(frame) < 3:
        return {
            "period_start": frame.iloc[0][frame.columns[0]] if not frame.empty else "",
            "period_end": frame.iloc[-1][frame.columns[0]] if not frame.empty else "",
            "slope": None,
            "p_value": None,
            "r_squared": None,
            "is_significant": False,
        }
    series = frame[value_column].astype(float)
    result = linregress(range(len(frame)), series)
    return {
        "period_start": frame.iloc[0][frame.columns[0]],
        "period_end": frame.iloc[-1][frame.columns[0]],
        "slope": float(result.slope),
        "p_value": float(result.pvalue),
        "r_squared": float(result.rvalue ** 2),
        "is_significant": bool(result.pvalue < 0.05),
    }


def build_sentiment_drift(sentiment_df: pd.DataFrame, p_threshold: float) -> pd.DataFrame:
    """Build city-level sentiment drift summaries."""
    if sentiment_df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "metric",
                "period_start",
                "period_end",
                "slope",
                "p_value",
                "r_squared",
                "is_significant",
            ]
        )
    rows: list[dict[str, object]] = []
    for (city, normalized_city, state), frame in sentiment_df.groupby(
        ["city", "normalized_city", "state"],
        dropna=False,
    ):
        ordered = frame.sort_values("year_month").reset_index(drop=True)
        metrics = _regress(ordered[["year_month", "mean_sentiment"]], "mean_sentiment")
        metrics.update(
            {
                "city": city,
                "normalized_city": normalized_city,
                "state": state,
                "metric": "mean_sentiment",
                "is_significant": bool((metrics["p_value"] or 1.0) < p_threshold),
            }
        )
        rows.append(metrics)
    return pd.DataFrame(rows)


def build_topic_drift(keyword_df: pd.DataFrame, p_threshold: float) -> pd.DataFrame:
    """Build city-keyword drift summaries."""
    if keyword_df.empty:
        return pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "keyword",
                "period_start",
                "period_end",
                "slope",
                "p_value",
                "r_squared",
                "is_significant",
            ]
        )
    rows: list[dict[str, object]] = []
    for keys, frame in keyword_df.groupby(
        ["city", "normalized_city", "state", "keyword"],
        dropna=False,
    ):
        city, normalized_city, state, keyword = keys
        ordered = frame.sort_values("year_quarter").reset_index(drop=True)
        metrics = _regress(ordered[["year_quarter", "relative_frequency"]], "relative_frequency")
        metrics.update(
            {
                "city": city,
                "normalized_city": normalized_city,
                "state": state,
                "keyword": keyword,
                "is_significant": bool((metrics["p_value"] or 1.0) < p_threshold),
            }
        )
        rows.append(metrics)
    return pd.DataFrame(rows)


def plot_heatmap(sentiment_df: pd.DataFrame, output_path: str) -> None:
    """Plot a city x month sentiment heatmap."""
    if sentiment_df.empty:
        save_placeholder_figure(Path(output_path), "Track C: Drift Heatmap")
        return
    pivot = sentiment_df.pivot_table(
        index="city",
        columns="year_month",
        values="mean_sentiment",
        aggfunc="mean",
    ).sort_index()
    fig, ax = plt.subplots(figsize=(12, max(4, len(pivot) * 0.4)))
    image = ax.imshow(pivot.fillna(0.0), aspect="auto", cmap="coolwarm")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
    ax.set_title("Track C: Sentiment Heatmap by City and Month")
    fig.colorbar(image, ax=ax, label="Mean Sentiment")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 6: Drift Detection")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    p_threshold = float(config.get("drift", {}).get("slope_p_threshold", 0.05))

    sentiment_path = paths.tables_dir / "track_c_s4_sentiment_by_city_month.parquet"
    keyword_path = paths.tables_dir / "track_c_s5_keyword_trends.parquet"
    sentiment_df = pd.read_parquet(sentiment_path) if sentiment_path.is_file() else pd.DataFrame()
    keyword_df = pd.read_parquet(keyword_path) if keyword_path.is_file() else pd.DataFrame()

    sentiment_drift = build_sentiment_drift(sentiment_df, p_threshold)
    topic_drift = build_topic_drift(keyword_df, p_threshold)

    write_parquet(
        sentiment_drift,
        paths.tables_dir / "track_c_s6_sentiment_drift_by_city.parquet",
    )
    write_parquet(
        topic_drift,
        paths.tables_dir / "track_c_s6_topic_drift_by_city.parquet",
    )
    plot_heatmap(sentiment_df, str(paths.figures_dir / "track_c_s6_drift_heatmap.png"))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
