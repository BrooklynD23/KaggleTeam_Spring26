"""Stage 5: Topic prevalence profiling for Track C."""

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
    load_analyzable_cities,
    load_review_text_sample,
    primary_category,
    quarter_label,
    resolve_paths,
    save_placeholder_figure,
    write_parquet,
)

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def build_keyword_trends(
    con: duckdb.DuckDBPyConnection,
    review_path: str,
    review_fact_path: str,
    sample_size: int,
    seed: int,
    keywords: list[str],
    analyzable_cities: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build keyword frequency and optional cluster summary outputs."""
    sample_df = load_review_text_sample(
        con,
        Path(review_path),
        Path(review_fact_path),
        sample_size,
        seed,
    )
    if sample_df.empty:
        empty_keywords = pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "primary_category",
                "year_quarter",
                "keyword",
                "frequency",
                "relative_frequency",
                "review_count",
            ]
        )
        empty_clusters = pd.DataFrame(columns=["cluster_id", "cluster_size", "top_terms"])
        return empty_keywords, empty_clusters

    sample_df["review_text"] = sample_df["review_text"].astype(str)
    sample_df["normalized_city"] = sample_df["city"].astype(str).str.strip().str.lower()
    if analyzable_cities:
        sample_df = sample_df.loc[
            sample_df["normalized_city"].isin(analyzable_cities)
        ].copy()
    sample_df["year_quarter"] = [
        quarter_label(year, month)
        for year, month in zip(sample_df["review_year"], sample_df["review_month"], strict=True)
    ]
    sample_df["primary_category"] = sample_df["categories"].apply(primary_category)

    keyword_frames: list[pd.DataFrame] = []
    lowered = sample_df["review_text"].str.lower()
    for keyword in keywords:
        keyword_df = sample_df.loc[
            lowered.str.contains(keyword.lower(), regex=False, na=False)
        ].copy()
        if keyword_df.empty:
            continue
        grouped = (
            keyword_df.groupby(
                ["city", "normalized_city", "state", "primary_category", "year_quarter"],
                dropna=False,
                as_index=False,
            )
            .size()
            .rename(columns={"size": "frequency"})
        )
        totals = (
            sample_df.groupby(
                ["city", "normalized_city", "state", "primary_category", "year_quarter"],
                dropna=False,
                as_index=False,
            )
            .size()
            .rename(columns={"size": "review_count"})
        )
        grouped = grouped.merge(
            totals,
            on=["city", "normalized_city", "state", "primary_category", "year_quarter"],
            how="left",
        )
        grouped["keyword"] = keyword
        grouped["relative_frequency"] = grouped["frequency"] / grouped["review_count"].clip(lower=1)
        keyword_frames.append(grouped)

    keyword_trends = (
        pd.concat(keyword_frames, ignore_index=True)
        if keyword_frames
        else pd.DataFrame(
            columns=[
                "city",
                "normalized_city",
                "state",
                "primary_category",
                "year_quarter",
                "frequency",
                "review_count",
                "keyword",
                "relative_frequency",
            ]
        )
    )
    cluster_summary = build_cluster_summary(sample_df)
    # keyword_trends and cluster_summary are aggregate-only; sample_df is not persisted.
    return keyword_trends, cluster_summary


def build_cluster_summary(sample_df: pd.DataFrame) -> pd.DataFrame:
    """Build a compact TF-IDF cluster summary when sklearn is available."""
    if sample_df.empty:
        return pd.DataFrame(columns=["cluster_id", "cluster_size", "top_terms"])
    try:
        from sklearn.cluster import KMeans
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        logger.warning("scikit-learn unavailable; writing empty TF-IDF cluster summary.")
        return pd.DataFrame(columns=["cluster_id", "cluster_size", "top_terms"])

    texts = sample_df["review_text"].astype(str).head(5000)
    if len(texts) < 10:
        return pd.DataFrame(columns=["cluster_id", "cluster_size", "top_terms"])

    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    matrix = vectorizer.fit_transform(texts)
    cluster_count = max(2, min(10, matrix.shape[0] // 100))
    if cluster_count >= matrix.shape[0]:
        cluster_count = max(2, matrix.shape[0] - 1)
    if cluster_count < 2:
        return pd.DataFrame(columns=["cluster_id", "cluster_size", "top_terms"])

    model = KMeans(n_clusters=cluster_count, n_init=10, random_state=42)
    labels = model.fit_predict(matrix)
    terms = vectorizer.get_feature_names_out()
    rows: list[dict[str, object]] = []
    for cluster_id in range(cluster_count):
        weights = model.cluster_centers_[cluster_id]
        top_terms = ", ".join(terms[weights.argsort()[::-1][:10]])
        rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_size": int((labels == cluster_id).sum()),
                "top_terms": top_terms,
            }
        )
    return pd.DataFrame(rows)


def plot_keyword_trends(keyword_df: pd.DataFrame, output_path: str) -> None:
    """Plot keyword relative-frequency trend lines for top keywords."""
    if keyword_df.empty:
        save_placeholder_figure(Path(output_path), "Track C: Keyword Trend Lines")
        return
    top_rows = (
        keyword_df.groupby("keyword")["frequency"]
        .sum()
        .sort_values(ascending=False)
        .head(4)
        .index.tolist()
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    for keyword in top_rows:
        frame = (
            keyword_df.loc[keyword_df["keyword"] == keyword]
            .groupby("year_quarter", as_index=False)["relative_frequency"]
            .mean()
            .sort_values("year_quarter")
        )
        ax.plot(frame["year_quarter"], frame["relative_frequency"], marker="o", label=keyword)
    ax.set_title("Track C: Keyword Trends Over Time")
    ax.set_ylabel("Relative Frequency")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 5: Topic Prevalence")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    sample_size = int(config.get("nlp", {}).get("sample_size", 100_000))
    seed = int(config.get("nlp", {}).get("random_seed", 42))
    keywords = [str(keyword) for keyword in config.get("nlp", {}).get("keyword_list", [])]

    con = duckdb.connect()
    try:
        keyword_df, cluster_df = build_keyword_trends(
            con,
            str(paths.review_path),
            str(paths.review_fact_path),
            sample_size,
            seed,
            keywords,
            load_analyzable_cities(paths),
        )
    finally:
        con.close()

    write_parquet(keyword_df, paths.tables_dir / "track_c_s5_keyword_trends.parquet")
    write_parquet(
        cluster_df,
        paths.tables_dir / "track_c_s5_tfidf_cluster_summary.parquet",
    )
    plot_keyword_trends(
        keyword_df,
        str(paths.figures_dir / "track_c_s5_keyword_trend_lines.png"),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
