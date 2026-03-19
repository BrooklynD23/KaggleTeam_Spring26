"""Shared helpers for Track C stage scripts."""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.db import connect_duckdb

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

BANNED_TEXT_COLUMNS = {"text", "review_text", "raw_text"}
POSITIVE_WORDS = {
    "amazing",
    "awesome",
    "best",
    "delicious",
    "excellent",
    "friendly",
    "good",
    "great",
    "love",
    "perfect",
}
NEGATIVE_WORDS = {
    "awful",
    "bad",
    "dirty",
    "hate",
    "horrible",
    "poor",
    "rude",
    "slow",
    "terrible",
    "worst",
}


@dataclass(frozen=True)
class TrackCPaths:
    """Resolved filesystem locations used by Track C."""

    curated_dir: Path
    tables_dir: Path
    figures_dir: Path
    logs_dir: Path
    review_fact_path: Path
    review_path: Path
    business_path: Path
    checkin_path: Path
    checkin_expanded_path: Path
    snapshot_metadata_path: Path


def _resolve(config: dict[str, Any], key: str) -> Path:
    raw = Path(config["paths"][key])
    return raw if raw.is_absolute() else PROJECT_ROOT / raw


def resolve_paths(config: dict[str, Any]) -> TrackCPaths:
    """Resolve configured Track C paths."""
    curated_dir = _resolve(config, "curated_dir")
    tables_dir = _resolve(config, "tables_dir")
    figures_dir = _resolve(config, "figures_dir")
    logs_dir = _resolve(config, "logs_dir")
    return TrackCPaths(
        curated_dir=curated_dir,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        logs_dir=logs_dir,
        review_fact_path=curated_dir / "review_fact.parquet",
        review_path=curated_dir / "review.parquet",
        business_path=curated_dir / "business.parquet",
        checkin_path=curated_dir / "checkin.parquet",
        checkin_expanded_path=curated_dir / "checkin_expanded.parquet",
        snapshot_metadata_path=curated_dir / "snapshot_metadata.json",
    )


def ensure_output_dirs(paths: TrackCPaths) -> None:
    """Create Track C output directories if needed."""
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write a dataframe to parquet, ensuring the parent directory exists.

    Raises ValueError if any banned text columns are present (no-raw-text contract).
    """
    banned_found = {col for col in df.columns if col.lower() in BANNED_TEXT_COLUMNS}
    if banned_found:
        raise ValueError(
            f"Refusing to write parquet with banned text columns {sorted(banned_found)} to {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info("Wrote %s (%d rows)", path, len(df))


def save_placeholder_figure(path: Path, title: str, message: str = "No data available") -> None:
    """Write a placeholder figure when there is nothing meaningful to plot."""
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.set_title(title)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    logger.info("Wrote placeholder %s", path)


def month_label(year: Any, month: Any) -> str:
    """Return a zero-padded year-month label."""
    try:
        return f"{int(year):04d}-{int(month):02d}"
    except (TypeError, ValueError):
        return ""


def quarter_label(year: Any, month: Any) -> str:
    """Return a year-quarter label."""
    try:
        year_i = int(year)
        month_i = int(month)
    except (TypeError, ValueError):
        return ""
    quarter = ((month_i - 1) // 3) + 1
    return f"{year_i:04d}-Q{quarter}"


def primary_category(categories: Any) -> str:
    """Extract the first category value from a Yelp categories string."""
    if categories is None or (isinstance(categories, float) and math.isnan(categories)):
        return "unknown"
    value = str(categories).strip()
    if not value:
        return "unknown"
    return value.split(",")[0].strip() or "unknown"


def load_snapshot_metadata(paths: TrackCPaths) -> dict[str, str]:
    """Load snapshot metadata when present."""
    if not paths.snapshot_metadata_path.is_file():
        return {}
    with open(paths.snapshot_metadata_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if "snapshot_reference_date" in payload:
        try:
            date.fromisoformat(str(payload["snapshot_reference_date"]))
        except ValueError:
            logger.warning(
                "snapshot_reference_date %r is not ISO formatted",
                payload["snapshot_reference_date"],
            )
    return {str(key): str(value) for key, value in payload.items()}


def load_analyzable_cities(paths: TrackCPaths) -> set[str]:
    """Load analyzable cities from Stage 1 when present."""
    stage1_path = paths.tables_dir / "track_c_s1_city_coverage.parquet"
    if not stage1_path.is_file():
        return set()
    pq_str = str(stage1_path).replace("\\", "/")
    con = connect_duckdb()
    try:
        rows = con.execute(
            f"""
            SELECT normalized_city
            FROM read_parquet('{pq_str}')
            WHERE COALESCE(is_analyzable, FALSE)
            """
        ).fetchall()
    finally:
        con.close()
    return {str(row[0]) for row in rows if row and row[0]}


def detect_language(text: str, seed: int = 42) -> str:
    """Best-effort language detection with a simple fallback.

    The seed is applied to langdetect's DetectorFactory for reproducibility;
    without it, langdetect uses random profile selection between calls.
    """
    stripped = text.strip()
    if not stripped:
        return "unknown"
    try:
        from langdetect import DetectorFactory, LangDetectException, detect

        DetectorFactory.seed = seed
        try:
            return str(detect(stripped))
        except LangDetectException:
            return "unknown"
    except ImportError:
        ascii_chars = sum(1 for char in stripped if ord(char) < 128)
        return "en" if ascii_chars / max(len(stripped), 1) >= 0.95 else "unknown"


def lexical_sentiment(text: str) -> float:
    """Compute a simple lexicon-based fallback sentiment score."""
    tokens = re.findall(r"[a-z']+", text.lower())
    if not tokens:
        return 0.0
    positive = sum(token in POSITIVE_WORDS for token in tokens)
    negative = sum(token in NEGATIVE_WORDS for token in tokens)
    return (positive - negative) / max(len(tokens), 1)


def sentiment_score(text: str, engine: str = "textblob") -> float:
    """Return a sentiment score using TextBlob when available."""
    if engine.lower() == "textblob":
        try:
            from textblob import TextBlob

            return float(TextBlob(text).sentiment.polarity)
        except ImportError:
            logger.warning("TextBlob unavailable; falling back to lexical sentiment.")
    return lexical_sentiment(text)


def load_review_text_sample(
    con: duckdb.DuckDBPyConnection,
    review_path: Path,
    review_fact_path: Path,
    sample_size: int,
    seed: int,
) -> pd.DataFrame:
    """Load raw review text, restricted to curated review_ids via semijoin."""
    if not review_path.is_file() or not review_fact_path.is_file():
        return pd.DataFrame(
            columns=[
                "review_id",
                "review_text",
                "business_id",
                "review_stars",
                "city",
                "state",
                "categories",
                "review_year",
                "review_month",
                "review_date",
                "text_word_count",
                "text_char_count",
            ]
        )
    rev_pq = str(review_path).replace("\\", "/")
    rf_pq = str(review_fact_path).replace("\\", "/")
    n_sample = max(int(sample_size), 1)

    ids_sql = f"""
        SELECT review_id
        FROM read_parquet(?)
        WHERE text IS NOT NULL AND LENGTH(TRIM(text)) > 0
        USING SAMPLE reservoir({n_sample} ROWS) REPEATABLE({int(seed)})
    """
    try:
        sampled_ids = con.execute(ids_sql, [rev_pq]).fetchdf()
    except Exception:
        sampled_ids = con.execute(
            ids_sql.replace("read_parquet(?)", f"read_parquet('{rev_pq}')", 1)
        ).fetchdf()
    con.register("_sampled_ids", sampled_ids)

    join_sql = """
        SELECT
            r.review_id,
            r.text AS review_text,
            rf.business_id,
            rf.review_stars,
            rf.city,
            rf.state,
            rf.categories,
            rf.review_year,
            rf.review_month,
            rf.review_date,
            rf.text_word_count,
            rf.text_char_count
        FROM read_parquet(?) AS r
        JOIN _sampled_ids AS s ON r.review_id = s.review_id
        JOIN read_parquet(?) AS rf ON r.review_id = rf.review_id
    """
    try:
        result = con.execute(join_sql, [rev_pq, rf_pq]).fetchdf()
    except Exception:
        fallback_sql = join_sql.replace("read_parquet(?)", f"read_parquet('{rev_pq}')", 1)
        fallback_sql = fallback_sql.replace("read_parquet(?)", f"read_parquet('{rf_pq}')", 1)
        result = con.execute(fallback_sql).fetchdf()
    con.unregister("_sampled_ids")
    return result


def drop_raw_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop any raw text columns before persisting parquet outputs."""
    columns = [
        column for column in df.columns
        if column.lower() not in BANNED_TEXT_COLUMNS
    ]
    return df.loc[:, columns].copy()


def describe_parquet_columns(
    con: duckdb.DuckDBPyConnection,
    parquet_path: Path,
) -> list[str]:
    """Return parquet column names via DuckDB schema introspection."""
    pq_str = str(parquet_path).replace("\\", "/")
    return [
        str(row[0])
        for row in con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{pq_str}')"
        ).fetchall()
    ]


def scan_track_c_text_leaks(paths: TrackCPaths) -> list[dict[str, str]]:
    """Return a soft list of banned text-column findings across Track C parquet outputs."""
    findings: list[dict[str, str]] = []
    con = connect_duckdb()
    try:
        for parquet_path in sorted(paths.tables_dir.glob("track_c_*.parquet")):
            columns = {name.lower() for name in describe_parquet_columns(con, parquet_path)}
            banned = sorted(columns & BANNED_TEXT_COLUMNS)
            findings.append(
                {
                    "artifact_path": str(parquet_path),
                    "status": "FAIL" if banned else "PASS",
                    "detail": (
                        "Found banned text columns: " + ", ".join(banned)
                        if banned
                        else "No banned text columns detected."
                    ),
                }
            )
    finally:
        con.close()
    return findings
