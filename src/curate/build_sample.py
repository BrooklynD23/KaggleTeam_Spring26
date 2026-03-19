"""Build a stratified sample from curated parquet for notebook EDA.

Usage:
    python -m src.curate.build_sample --config configs/base.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from pathlib import Path
from typing import Any

import polars as pl

from src.common.config import load_config

logger = logging.getLogger(__name__)

CURATED_FILES = [
    "review_fact.parquet",
    "review_fact_track_b.parquet",
    "review.parquet",
    "business.parquet",
    "user.parquet",
    "tip.parquet",
    "checkin.parquet",
    "checkin_expanded.parquet",
]
SNAPSHOT_METADATA = "snapshot_metadata.json"
SAMPLE_MANIFEST = "sample_manifest.json"
DEFAULT_SAMPLE_SIZE = 20_000
STRATA_COLS = ["review_year", "review_stars"]


def _stratified_sample(
    df: pl.DataFrame,
    strata: list[str],
    n: int,
    seed: int,
) -> pl.DataFrame:
    """Sample n rows stratified by strata columns. Uses proportional allocation."""
    if len(df) <= n:
        return df

    # Proportional allocation per stratum
    counts = df.group_by(strata).len()
    total = counts["len"].sum()
    counts = counts.with_columns(
        (pl.col("len") * n / total).ceil().cast(pl.Int64).alias("target")
    )
    # Cap each stratum at its actual size
    counts = counts.with_columns(
        pl.min_horizontal("len", "target").alias("take")
    )

    sampled: list[pl.DataFrame] = []
    for row in counts.iter_rows(named=True):
        mask = pl.lit(True)
        for col in strata:
            mask = mask & (pl.col(col) == row[col])
        stratum_df = df.filter(mask)
        take = min(int(row["take"]), len(stratum_df))
        if take > 0:
            sampled.append(stratum_df.sample(n=take, seed=seed, shuffle=True))

    out = pl.concat(sampled)
    # If we overshot due to ceiling, trim
    if len(out) > n:
        out = out.sample(n=n, seed=seed + 1, shuffle=True)
    return out


def run(config: dict[str, Any]) -> None:
    """Build stratified sample from curated parquet."""
    paths = config["paths"]
    sample_cfg = config.get("sample", {})
    curated_dir = Path(paths["curated_dir"])
    sample_dir = Path(sample_cfg.get("sample_dir", "data/sample"))
    if not curated_dir.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        curated_dir = repo_root / curated_dir
        sample_dir = repo_root / sample_dir

    sample_size = sample_cfg.get("sample_size", DEFAULT_SAMPLE_SIZE)
    seed = config.get("random_seed", 42)
    strata = sample_cfg.get("sample_strata", STRATA_COLS)

    review_fact_path = curated_dir / "review_fact.parquet"
    if not review_fact_path.is_file():
        raise FileNotFoundError(
            f"Curated review_fact.parquet not found at {review_fact_path}. "
            "Run shared pipeline (build_review_fact) first."
        )

    logger.info("Loading review_fact from %s", review_fact_path)
    rf = pl.read_parquet(review_fact_path)

    sampled_rf = _stratified_sample(rf, strata, sample_size, seed)
    sampled_ids = set(sampled_rf["review_id"].to_list())
    sampled_business_ids = set(sampled_rf["business_id"].to_list())
    sampled_user_ids = set(sampled_rf["user_id"].to_list())

    sample_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "sample_size": len(sampled_rf),
        "seed": seed,
        "strata": strata,
        "row_counts": {},
    }

    # Write review_fact sample
    sampled_rf.write_parquet(sample_dir / "review_fact.parquet", compression="zstd")
    manifest["row_counts"]["review_fact"] = len(sampled_rf)
    logger.info("Wrote review_fact.parquet (%d rows)", len(sampled_rf))

    # Semi-join review_fact_track_b
    rf_track_b_path = curated_dir / "review_fact_track_b.parquet"
    if rf_track_b_path.is_file():
        rftb = pl.read_parquet(rf_track_b_path)
        rftb_sampled = rftb.filter(pl.col("review_id").is_in(list(sampled_ids)))
        rftb_sampled.write_parquet(
            sample_dir / "review_fact_track_b.parquet", compression="zstd"
        )
        manifest["row_counts"]["review_fact_track_b"] = len(rftb_sampled)
        logger.info("Wrote review_fact_track_b.parquet (%d rows)", len(rftb_sampled))

    # Filter entity tables by sampled business_id and user_id
    for name, id_col in [
        ("business", "business_id"),
        ("user", "user_id"),
        ("review", "review_id"),
    ]:
        path = curated_dir / f"{name}.parquet"
        if not path.is_file():
            continue
        df = pl.read_parquet(path)
        if id_col == "review_id":
            ids = sampled_ids
        elif id_col == "business_id":
            ids = sampled_business_ids
        else:
            ids = sampled_user_ids
        filtered = df.filter(pl.col(id_col).is_in(list(ids)))
        filtered.write_parquet(sample_dir / f"{name}.parquet", compression="zstd")
        manifest["row_counts"][name] = len(filtered)
        logger.info("Wrote %s.parquet (%d rows)", name, len(filtered))

    # tip: filter by both business_id and user_id
    tip_path = curated_dir / "tip.parquet"
    if tip_path.is_file():
        tip = pl.read_parquet(tip_path)
        tip_filtered = tip.filter(
            pl.col("business_id").is_in(list(sampled_business_ids))
            & pl.col("user_id").is_in(list(sampled_user_ids))
        )
        tip_filtered.write_parquet(sample_dir / "tip.parquet", compression="zstd")
        manifest["row_counts"]["tip"] = len(tip_filtered)
        logger.info("Wrote tip.parquet (%d rows)", len(tip_filtered))

    # checkin and checkin_expanded: filter by business_id
    for name in ["checkin", "checkin_expanded"]:
        path = curated_dir / f"{name}.parquet"
        if not path.is_file():
            continue
        df = pl.read_parquet(path)
        filtered = df.filter(pl.col("business_id").is_in(list(sampled_business_ids)))
        filtered.write_parquet(sample_dir / f"{name}.parquet", compression="zstd")
        manifest["row_counts"][name] = len(filtered)
        logger.info("Wrote %s.parquet (%d rows)", name, len(filtered))

    # Copy snapshot_metadata.json
    snapshot_src = curated_dir / SNAPSHOT_METADATA
    if snapshot_src.is_file():
        shutil.copy2(snapshot_src, sample_dir / SNAPSHOT_METADATA)
        logger.info("Copied %s", SNAPSHOT_METADATA)

    # Write sample_manifest.json
    manifest_path = sample_dir / SAMPLE_MANIFEST
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    logger.info("Wrote %s", manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build stratified sample from curated parquet for notebook EDA."
    )
    parser.add_argument("--config", required=True, help="Path to config YAML")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    config = load_config(args.config)

    run(config)


if __name__ == "__main__":
    main()
