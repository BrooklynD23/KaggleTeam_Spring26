"""Stage 3: Text normalization profiling for Track C."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import duckdb
import pandas as pd

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_c.common import (
    detect_language,
    ensure_output_dirs,
    load_review_text_sample,
    resolve_paths,
    write_parquet,
)

logger = logging.getLogger(__name__)

HTML_PATTERN = re.compile(r"<[^>]+>|&[a-z]+;", re.IGNORECASE)


def build_text_outputs(
    con: duckdb.DuckDBPyConnection,
    review_path: str,
    review_fact_path: str,
    sample_size: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build aggregate text-quality outputs from a semijoined text sample."""
    sample_df = load_review_text_sample(
        con,
        Path(review_path),
        Path(review_fact_path),
        sample_size,
        seed,
    )
    if sample_df.empty:
        empty_stats = pd.DataFrame(
            columns=["metric_name", "metric_value", "sample_size"]
        )
        empty_lang = pd.DataFrame(columns=["language", "review_count", "fraction"])
        return empty_stats, empty_lang

    sample_df["review_text"] = sample_df["review_text"].astype(str)
    sample_df["language"] = sample_df["review_text"].apply(detect_language)
    sample_df["non_ascii_rate"] = sample_df["review_text"].apply(
        lambda text: (
            sum(1 for char in text if ord(char) >= 128) / max(len(text), 1)
        )
    )
    sample_df["html_artifact_flag"] = sample_df["review_text"].str.contains(
        HTML_PATTERN,
        na=False,
    )

    metrics = [
        {
            "metric_name": "sample_size",
            "metric_value": float(len(sample_df)),
            "sample_size": len(sample_df),
        },
        {
            "metric_name": "mean_words",
            "metric_value": float(sample_df["text_word_count"].mean()),
            "sample_size": len(sample_df),
        },
        {
            "metric_name": "median_words",
            "metric_value": float(sample_df["text_word_count"].median()),
            "sample_size": len(sample_df),
        },
        {
            "metric_name": "p95_words",
            "metric_value": float(sample_df["text_word_count"].quantile(0.95)),
            "sample_size": len(sample_df),
        },
        {
            "metric_name": "mean_non_ascii_rate",
            "metric_value": float(sample_df["non_ascii_rate"].mean()),
            "sample_size": len(sample_df),
        },
        {
            "metric_name": "html_artifact_rate",
            "metric_value": float(sample_df["html_artifact_flag"].mean()),
            "sample_size": len(sample_df),
        },
    ]
    stats_df = pd.DataFrame(metrics)
    lang_df = (
        sample_df.groupby("language", dropna=False)
        .size()
        .reset_index(name="review_count")
        .sort_values("review_count", ascending=False)
    )
    lang_df["fraction"] = lang_df["review_count"] / len(sample_df)

    # stats_df and lang_df are aggregate-only; sample_df is not persisted.
    return stats_df, lang_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 3: Text Normalization")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    sample_size = int(config.get("nlp", {}).get("sample_size", 100_000))
    seed = int(config.get("nlp", {}).get("random_seed", 42))

    con = connect_duckdb(config)
    try:
        stats_df, lang_df = build_text_outputs(
            con,
            str(paths.review_path),
            str(paths.review_fact_path),
            sample_size,
            seed,
        )
    finally:
        con.close()

    write_parquet(stats_df, paths.tables_dir / "track_c_s3_text_stats.parquet")
    write_parquet(
        lang_df,
        paths.tables_dir / "track_c_s3_language_detection.parquet",
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
