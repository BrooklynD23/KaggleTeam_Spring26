"""CLI entry point for loading Yelp NDJSON files into DuckDB.

Usage:
    python -m src.ingest.load_yelp_json --config configs/base.yaml
"""

import argparse
import logging
import tarfile
import time
from pathlib import Path
from typing import Any

import duckdb

from src.common.config import load_config
from src.ingest.validate_json_structure import validate_first_n_lines

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# DuckDB table schemas keyed by entity name.
# Column tuples: (column_name, duckdb_type, source_json_key_or_None)
SCHEMAS: dict[str, list[tuple[str, str, str | None]]] = {
    "business": [
        ("business_id", "VARCHAR", None),
        ("name", "VARCHAR", None),
        ("address", "VARCHAR", None),
        ("city", "VARCHAR", None),
        ("state", "VARCHAR", None),
        ("postal_code", "VARCHAR", None),
        ("latitude", "DOUBLE", None),
        ("longitude", "DOUBLE", None),
        ("stars", "DOUBLE", None),
        ("review_count", "INTEGER", None),
        ("is_open", "INTEGER", None),
        ("attributes", "JSON", None),
        ("categories", "VARCHAR", None),
        ("hours", "JSON", None),
    ],
    "review": [
        ("review_id", "VARCHAR", None),
        ("user_id", "VARCHAR", None),
        ("business_id", "VARCHAR", None),
        ("stars", "DOUBLE", None),
        ("review_date", "DATE", "date"),
        ("text", "VARCHAR", None),
        ("useful", "INTEGER", None),
        ("funny", "INTEGER", None),
        ("cool", "INTEGER", None),
    ],
    "user": [
        ("user_id", "VARCHAR", None),
        ("name", "VARCHAR", None),
        ("review_count", "INTEGER", None),
        ("yelping_since", "DATE", None),
        ("useful", "INTEGER", None),
        ("funny", "INTEGER", None),
        ("cool", "INTEGER", None),
        ("elite", "VARCHAR", None),
        ("friends", "VARCHAR", None),
        ("fans", "INTEGER", None),
        ("average_stars", "DOUBLE", None),
        ("compliment_hot", "INTEGER", None),
        ("compliment_more", "INTEGER", None),
        ("compliment_profile", "INTEGER", None),
        ("compliment_cute", "INTEGER", None),
        ("compliment_list", "INTEGER", None),
        ("compliment_note", "INTEGER", None),
        ("compliment_plain", "INTEGER", None),
        ("compliment_cool", "INTEGER", None),
        ("compliment_funny", "INTEGER", None),
        ("compliment_writer", "INTEGER", None),
        ("compliment_photos", "INTEGER", None),
    ],
    "tip": [
        ("user_id", "VARCHAR", None),
        ("business_id", "VARCHAR", None),
        ("text", "VARCHAR", None),
        ("tip_date", "DATE", "date"),
        ("compliment_count", "INTEGER", None),
    ],
    "checkin": [
        ("business_id", "VARCHAR", None),
        ("checkin_dates", "VARCHAR", "date"),
    ],
}


def _build_column_select(schema: list[tuple[str, str, str | None]]) -> str:
    """Build the SELECT column list for read_ndjson_auto, renaming as needed."""
    parts: list[str] = []
    for col_name, col_type, source_key in schema:
        src = source_key if source_key else col_name
        if src != col_name:
            parts.append(f'"{src}"::{col_type} AS {col_name}')
        else:
            parts.append(f'"{src}"::{col_type} AS {col_name}')
    return ", ".join(parts)


def _extract_tar(tar_path: Path, raw_dir: Path) -> None:
    """Extract tar archive to raw_dir if JSON files are not already present."""
    existing_jsons = list(raw_dir.glob("yelp_academic_dataset_*.json"))
    if len(existing_jsons) >= 5:
        logger.info("Raw JSON files already present in %s, skipping extraction", raw_dir)
        return

    if not tar_path.is_file():
        raise FileNotFoundError(f"Tar archive not found: {tar_path}")

    logger.info("Extracting %s to %s", tar_path, raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(tar_path, "r") as tf:
        for member in tf.getmembers():
            if member.isfile() and member.name.endswith(".json"):
                member.name = Path(member.name).name
                tf.extract(member, path=raw_dir)
                logger.info("  Extracted %s", member.name)

    logger.info("Extraction complete")


def _resolve_tar_path(project_root: Path, configured_tar_path: str) -> Path:
    """Resolve ingestion tar path with repo-first then legacy fallback behavior."""
    tar_cfg = Path(configured_tar_path)
    if tar_cfg.is_absolute():
        return tar_cfg

    repo_relative = project_root / tar_cfg
    legacy_cowork = project_root / "CoWork Planning" / tar_cfg
    if repo_relative.is_file():
        return repo_relative
    if legacy_cowork.is_file():
        return legacy_cowork
    return repo_relative


def _load_entity(
    con: duckdb.DuckDBPyConnection,
    entity_name: str,
    source_file: str,
    raw_dir: Path,
) -> int:
    """Load a single entity from NDJSON into a DuckDB table.

    Returns the row count of the loaded table.
    """
    schema = SCHEMAS[entity_name]
    filepath = raw_dir / source_file
    if not filepath.is_file():
        raise FileNotFoundError(f"Source file not found: {filepath}")

    col_select = _build_column_select(schema)
    file_str = str(filepath).replace("\\", "/")

    table_name = f'"{entity_name}"' if entity_name == "user" else entity_name

    sql = (
        f"CREATE OR REPLACE TABLE {table_name} AS "
        f"SELECT {col_select} "
        f"FROM read_ndjson_auto('{file_str}')"
    )

    logger.info("Loading entity '%s' from %s", entity_name, filepath)
    t0 = time.perf_counter()
    con.execute(sql)
    elapsed = time.perf_counter() - t0

    row_count: int = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]  # type: ignore[index]
    logger.info(
        "Loaded %s: %d rows in %.1f seconds",
        entity_name, row_count, elapsed,
    )
    return row_count


def run(config: dict[str, Any]) -> None:
    """Execute the full ingestion pipeline."""
    paths_cfg = config["paths"]
    ingest_cfg = config["ingestion"]
    entities_cfg: list[dict[str, Any]] = config["entities"]

    raw_dir = PROJECT_ROOT / paths_cfg["raw_dir"]
    db_path = PROJECT_ROOT / paths_cfg["db_path"]

    tar_path = _resolve_tar_path(PROJECT_ROOT, ingest_cfg["tar_path"])

    # Step 1: Extract tar
    _extract_tar(tar_path, raw_dir)

    # Step 2: Validate JSON structure
    for ent in entities_cfg:
        name = ent["name"]
        source = ent["source_file"]
        result = validate_first_n_lines(raw_dir / source, name)
        if result["status"] == "FAIL":
            logger.warning(
                "Validation issues for '%s': %s",
                name, result["missing_key_issues"],
            )

    # Step 3: Load into DuckDB
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))

    memory_limit = ingest_cfg.get("memory_limit_gb", 4)
    threads = ingest_cfg.get("threads", 4)
    con.execute(f"SET memory_limit = '{memory_limit}GB'")
    con.execute(f"SET threads = {threads}")
    logger.info("DuckDB memory_limit=%dGB, threads=%d", memory_limit, threads)

    total_t0 = time.perf_counter()
    for ent in entities_cfg:
        _load_entity(con, ent["name"], ent["source_file"], raw_dir)

    total_elapsed = time.perf_counter() - total_t0
    logger.info("All entities loaded in %.1f seconds", total_elapsed)

    con.close()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Load Yelp NDJSON files into DuckDB",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to YAML config file",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    log_level = config.get("log_level", "INFO")
    logging.getLogger().setLevel(getattr(logging, log_level))

    run(config)


if __name__ == "__main__":
    main()
