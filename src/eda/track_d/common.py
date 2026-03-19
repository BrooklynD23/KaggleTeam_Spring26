"""Shared helpers for Track D stage scripts."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import duckdb
import pandas as pd

from src.common.db import connect_duckdb
from src.common.helpers import extract_price_range, parse_jsonish, primary_category  # noqa: F401
from src.common.parquet_io import read_parquet_pandas

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class TrackDPaths:
    """Resolved filesystem locations used by Track D."""

    curated_dir: Path
    tables_dir: Path
    figures_dir: Path
    logs_dir: Path
    review_fact_path: Path
    business_path: Path
    tip_path: Path
    checkin_path: Path
    checkin_expanded_path: Path


def _resolve(config: dict[str, Any], key: str) -> Path:
    raw = Path(config["paths"][key])
    return raw if raw.is_absolute() else PROJECT_ROOT / raw


def resolve_paths(config: dict[str, Any]) -> TrackDPaths:
    """Resolve configured Track D paths."""
    curated_dir = _resolve(config, "curated_dir")
    tables_dir = _resolve(config, "tables_dir")
    figures_dir = _resolve(config, "figures_dir")
    logs_dir = _resolve(config, "logs_dir")
    return TrackDPaths(
        curated_dir=curated_dir,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        logs_dir=logs_dir,
        review_fact_path=curated_dir / "review_fact.parquet",
        business_path=curated_dir / "business.parquet",
        tip_path=curated_dir / "tip.parquet",
        checkin_path=curated_dir / "checkin.parquet",
        checkin_expanded_path=curated_dir / "checkin_expanded.parquet",
    )


def ensure_output_dirs(paths: TrackDPaths) -> None:
    """Create Track D output directories if needed."""
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)


def list_track_d_artifacts(paths: TrackDPaths) -> list[Path]:
    """Return current Track D artifact paths in tables and logs."""
    artifacts = list(paths.tables_dir.glob("track_d_*")) + list(paths.logs_dir.glob("track_d_*"))
    return sorted(path for path in artifacts if path.is_file())


def load_track_a_splits(config: dict[str, Any], tables_dir: Path) -> tuple[str, str, str]:
    """Load Track A splits, respecting strict mode when the shared helper exists."""
    from src.common import artifacts

    con = connect_duckdb()
    try:
        strict_loader = getattr(artifacts, "load_splits_strict", None)
        if strict_loader is not None:
            return strict_loader(con, tables_dir, config)

        t1, t2, source = artifacts.load_candidate_splits(con, tables_dir, config)
        require = bool(config.get("splits", {}).get("require_stage5_artifact", False))
        if source == "config" and require:
            raise RuntimeError(
                "Track D requires Track A Stage 5 split artifact "
                "(track_a_s5_candidate_splits.parquet) but it was not found. "
                f"Placeholder dates t1={t1}, t2={t2} were NOT used."
            )
        return t1, t2, source
    finally:
        con.close()


def load_parquet(path: Path, sql: str | None = None, params: Iterable[Any] | None = None) -> pd.DataFrame:
    """Read a parquet-backed query into a DataFrame.

    When *sql* is ``None`` the file is read via Polars (no DuckDB).
    When *sql* is provided, DuckDB is used for the custom query.
    """
    if sql is None:
        return read_parquet_pandas(path)

    pq_str = str(path).replace("\\", "/")
    con = connect_duckdb()
    try:
        sql_inlined = sql.replace("read_parquet(?)", f"read_parquet('{pq_str}')")
        param_list = list(params or [])
        remaining = param_list[1:] if param_list and "read_parquet(?)" in sql else param_list
        return con.execute(sql_inlined, remaining).fetchdf() if remaining else con.execute(sql_inlined).fetchdf()
    finally:
        con.close()


def count_attributes(attributes_raw: Any) -> int:
    """Count non-empty business attributes."""
    attributes = parse_jsonish(attributes_raw)
    return sum(1 for value in attributes.values() if value not in {None, "", "None"})


def assign_business_cohort_label(
    prior_review_count: int,
    thresholds: dict[str, int],
) -> str:
    """Map an as-of business review count to a Track D1 cohort label."""
    sparse_max = int(thresholds.get("sparse_history", 3))
    emerging_max = int(thresholds.get("emerging", 10))
    if prior_review_count <= int(thresholds.get("zero_history", 0)):
        return "zero_history"
    if prior_review_count <= sparse_max:
        return "sparse_history"
    if prior_review_count <= emerging_max:
        return "emerging"
    return "established"


def assign_user_cohort_label(prior_total_interaction_count: int) -> str:
    """Map an as-of user interaction count to a Track D2 cohort label."""
    if prior_total_interaction_count <= 0:
        return "zero_history"
    if prior_total_interaction_count == 1:
        return "first_interaction"
    if prior_total_interaction_count <= 3:
        return "early"
    return "established"


def feature_coverage_frame(
    df: pd.DataFrame,
    group_col: str,
    feature_cols: list[str],
    *,
    subtrack: str,
) -> pd.DataFrame:
    """Compute non-null feature coverage by cohort-like group."""
    if df.empty:
        return pd.DataFrame(
            columns=["subtrack", group_col, "feature_name", "coverage_rate", "non_null_count", "row_count"]
        )

    rows: list[dict[str, Any]] = []
    grouped = df.groupby(group_col, dropna=False)
    for label, chunk in grouped:
        row_count = len(chunk)
        for feature in feature_cols:
            non_null_count = int(chunk[feature].notna().sum())
            rows.append(
                {
                    "subtrack": subtrack,
                    group_col: label,
                    "feature_name": feature,
                    "coverage_rate": non_null_count / row_count if row_count else 0.0,
                    "non_null_count": non_null_count,
                    "row_count": row_count,
                }
            )
    return pd.DataFrame(rows)


def load_checkins(paths: TrackDPaths) -> pd.DataFrame:
    """Load expanded checkins or derive them from raw checkin strings."""
    if paths.checkin_expanded_path.is_file():
        df = load_parquet(paths.checkin_expanded_path)
        if "checkin_date" in df.columns:
            df["checkin_date"] = pd.to_datetime(df["checkin_date"])
        return df

    if not paths.checkin_path.is_file():
        return pd.DataFrame(columns=["business_id", "checkin_date"])

    raw = load_parquet(paths.checkin_path)
    if raw.empty:
        return pd.DataFrame(columns=["business_id", "checkin_date"])

    rows: list[dict[str, Any]] = []
    for item in raw.itertuples(index=False):
        dates_value = getattr(item, "checkin_dates", None)
        if dates_value is None:
            continue
        for piece in str(dates_value).split(","):
            date_text = piece.strip()
            if not date_text:
                continue
            parsed = pd.to_datetime(date_text, errors="coerce")
            if pd.isna(parsed):
                continue
            rows.append({"business_id": getattr(item, "business_id"), "checkin_date": parsed.normalize()})
    return pd.DataFrame(rows)


def read_text(path: Path) -> str:
    """Read text using UTF-8 with permissive fallback."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
