"""Shared helpers for Track E stage scripts."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from src.common.helpers import extract_price_range, parse_jsonish, primary_category  # noqa: F401

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Minimum group size for any reported aggregate — enforced globally.
MIN_GROUP_SIZE_DEFAULT = 10

# Banned text columns — same contract as Track C.
BANNED_TEXT_COLUMNS = {"text", "review_text", "raw_text"}

# Forbidden demographic inference column names.
FORBIDDEN_DEMOGRAPHIC_COLUMNS = {"gender", "race", "income", "ethnicity", "nationality"}


@dataclass(frozen=True)
class TrackEPaths:
    """Resolved filesystem locations used by Track E."""

    curated_dir: Path
    tables_dir: Path
    figures_dir: Path
    logs_dir: Path
    review_fact_path: Path
    business_path: Path
    user_path: Path


def _resolve(config: dict[str, Any], key: str) -> Path:
    raw = Path(config["paths"][key])
    return raw if raw.is_absolute() else PROJECT_ROOT / raw


def resolve_paths(config: dict[str, Any]) -> TrackEPaths:
    """Resolve configured Track E paths."""
    curated_dir = _resolve(config, "curated_dir")
    tables_dir = _resolve(config, "tables_dir")
    figures_dir = _resolve(config, "figures_dir")
    logs_dir = _resolve(config, "logs_dir")
    return TrackEPaths(
        curated_dir=curated_dir,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        logs_dir=logs_dir,
        review_fact_path=curated_dir / "review_fact.parquet",
        business_path=curated_dir / "business.parquet",
        user_path=curated_dir / "user.parquet",
    )


def ensure_output_dirs(paths: TrackEPaths) -> None:
    """Create Track E output directories if needed."""
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)


def write_parquet(df: pd.DataFrame, path: Path, *, min_group_size: int = 0) -> None:
    """Write DataFrame to parquet with optional aggregate group-size enforcement.

    Args:
        df: DataFrame to write.
        path: Output path.
        min_group_size: If > 0, this is informational only — caller should have
            already called enforce_min_group_size before writing. This parameter
            is kept for API consistency.

    Raises:
        ValueError: If any banned column names are found (raw text) or forbidden
            demographic inference column names are found.
    """
    # No-raw-text contract
    banned = {col for col in df.columns if col.lower() in BANNED_TEXT_COLUMNS}
    if banned:
        raise ValueError(f"Refusing to write banned text columns {sorted(banned)}")

    # No demographic inference columns
    demographic = {col for col in df.columns if col.lower() in FORBIDDEN_DEMOGRAPHIC_COLUMNS}
    if demographic:
        raise ValueError(f"Refusing to write forbidden demographic columns {sorted(demographic)}")

    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    logger.info("Wrote %s (%d rows)", path, len(df))


def load_parquet(
    path: Path,
    sql: str | None = None,
    params: list[Any] | None = None,
) -> pd.DataFrame:
    """Read a parquet-backed query into a DataFrame."""
    con = duckdb.connect()
    try:
        if sql is None:
            return con.execute("SELECT * FROM read_parquet(?)", [str(path)]).fetchdf()
        return con.execute(sql, params or []).fetchdf()
    finally:
        con.close()


def list_track_e_artifacts(paths: TrackEPaths) -> list[Path]:
    """Return current Track E artifact paths in tables, figures, and logs."""
    artifacts = (
        list(paths.tables_dir.glob("track_e_*"))
        + list(paths.figures_dir.glob("track_e_*"))
        + list(paths.logs_dir.glob("track_e_*"))
    )
    return sorted(path for path in artifacts if path.is_file())


def save_placeholder_figure(path: Path, title: str, message: str = "No data available") -> None:
    """Save a placeholder figure when no data is available to plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=14, color="gray")
    ax.set_title(title)
    ax.set_xticks([])
    ax.set_yticks([])
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    logger.info("Wrote placeholder figure %s", path)


def enforce_min_group_size(
    df: pd.DataFrame,
    count_col: str,
    min_size: int,
) -> pd.DataFrame:
    """Filter rows where the group count is below the minimum threshold.

    This enforces the aggregate-only reporting constraint for Track E.
    Returns a new DataFrame (immutable pattern).
    """
    if min_size <= 0 or count_col not in df.columns:
        return df
    filtered = df.loc[df[count_col] >= min_size].copy()
    dropped = len(df) - len(filtered)
    if dropped > 0:
        logger.info(
            "Dropped %d subgroups below min_group_size=%d (column=%s)",
            dropped,
            min_size,
            count_col,
        )
    return filtered


def assign_price_tier(price_range: int | None, config: dict[str, Any]) -> str:
    """Map a RestaurantsPriceRange2 integer to a configured label.

    Returns the missing label for None values.
    """
    if price_range is None:
        return config["subgroups"]["price_tier_missing_label"]
    labels = config["subgroups"]["price_tier_labels"]
    return labels.get(price_range, labels.get(str(price_range), config["subgroups"]["price_tier_missing_label"]))


def assign_review_volume_tier(review_count: int, boundaries: list[int]) -> str:
    """Map a business review count to a volume tier label.

    boundaries=[10, 50] creates tiers: "<10", "10-50", "50+"
    """
    sorted_boundaries = sorted(boundaries)
    for i, boundary in enumerate(sorted_boundaries):
        if review_count < boundary:
            if i == 0:
                return f"<{boundary}"
            return f"{sorted_boundaries[i - 1]}-{boundary}"
    return f"{sorted_boundaries[-1]}+"
