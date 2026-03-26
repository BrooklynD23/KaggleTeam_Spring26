#!/usr/bin/env python3
"""Fail-closed verifier for multimodal photo-intake artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import polars as pl

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.multimodal.photo_intake_contract import (  # noqa: E402
    IMAGE_PATH_MANIFEST_COLUMNS,
    PHOTO_METADATA_COLUMNS,
    REASON_CODES,
    STATUS_CODES,
)


class VerificationError(RuntimeError):
    """Raised when verification checks fail."""


REQUIRED_FILES = (
    "manifest.json",
    "validation_report.json",
    "photo_metadata.parquet",
    "image_path_manifest.parquet",
)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise VerificationError(f"Expected JSON object at {path}")
    return payload


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def _check_row_count_shape(row_counts: dict[str, Any]) -> None:
    expected_keys = {"total", *STATUS_CODES}
    _assert(
        set(row_counts.keys()) == expected_keys,
        "row_counts keys mismatch: "
        f"expected {sorted(expected_keys)}, got {sorted(row_counts.keys())}",
    )
    for key in sorted(expected_keys):
        value = row_counts[key]
        _assert(
            isinstance(value, int) and value >= 0,
            f"row_counts[{key!r}] must be a non-negative integer (got {value!r})",
        )


def _check_integrity_shape(integrity: dict[str, Any]) -> None:
    expected_keys = set(REASON_CODES)
    _assert(
        set(integrity.keys()) == expected_keys,
        "integrity_counters keys mismatch: "
        f"expected {sorted(expected_keys)}, got {sorted(integrity.keys())}",
    )
    for key in sorted(expected_keys):
        value = integrity[key]
        _assert(
            isinstance(value, int) and value >= 0,
            f"integrity_counters[{key!r}] must be a non-negative integer (got {value!r})",
        )


def _resolve_artifact_path(root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return (root / candidate).resolve()


def verify(root: Path) -> None:
    for filename in REQUIRED_FILES:
        path = root / filename
        _assert(path.is_file(), f"Missing required artifact: {path}")

    manifest = _load_json(root / "manifest.json")
    validation = _load_json(root / "validation_report.json")

    _assert(validation.get("status") == "pass", "validation_report status is not 'pass'")
    errors = validation.get("errors", [])
    _assert(isinstance(errors, list), "validation_report.errors must be a list")
    _assert(len(errors) == 0, f"validation_report.errors must be empty (got {errors!r})")

    manifest_row_counts = manifest.get("row_counts")
    validation_row_counts = validation.get("row_counts")
    _assert(isinstance(manifest_row_counts, dict), "manifest.row_counts must be an object")
    _assert(isinstance(validation_row_counts, dict), "validation_report.row_counts must be an object")
    _check_row_count_shape(manifest_row_counts)
    _check_row_count_shape(validation_row_counts)
    _assert(
        manifest_row_counts == validation_row_counts,
        "manifest.row_counts and validation_report.row_counts differ",
    )

    manifest_integrity = manifest.get("integrity_counters")
    validation_integrity = validation.get("integrity_counters")
    _assert(
        isinstance(manifest_integrity, dict),
        "manifest.integrity_counters must be an object",
    )
    _assert(
        isinstance(validation_integrity, dict),
        "validation_report.integrity_counters must be an object",
    )
    _check_integrity_shape(manifest_integrity)
    _check_integrity_shape(validation_integrity)
    _assert(
        manifest_integrity == validation_integrity,
        "manifest.integrity_counters and validation_report.integrity_counters differ",
    )

    photo_metadata_path = root / "photo_metadata.parquet"
    image_manifest_path = root / "image_path_manifest.parquet"

    artifacts = manifest.get("artifacts")
    _assert(isinstance(artifacts, dict), "manifest.artifacts must be an object")
    expected_artifact_map = {
        "photo_metadata_parquet": photo_metadata_path,
        "image_path_manifest_parquet": image_manifest_path,
        "validation_report_json": root / "validation_report.json",
    }
    for key, expected_path in expected_artifact_map.items():
        configured = _resolve_artifact_path(root, artifacts.get(key))
        _assert(configured is not None, f"manifest.artifacts.{key} is missing")
        _assert(
            configured.resolve() == expected_path.resolve(),
            f"manifest.artifacts.{key} points to {configured}, expected {expected_path}",
        )

    photo_df = pl.read_parquet(photo_metadata_path)
    image_df = pl.read_parquet(image_manifest_path)

    _assert(
        tuple(photo_df.columns) == PHOTO_METADATA_COLUMNS,
        "photo_metadata parquet columns mismatch: "
        f"expected {PHOTO_METADATA_COLUMNS}, got {tuple(photo_df.columns)}",
    )
    _assert(
        tuple(image_df.columns) == IMAGE_PATH_MANIFEST_COLUMNS,
        "image_path_manifest parquet columns mismatch: "
        f"expected {IMAGE_PATH_MANIFEST_COLUMNS}, got {tuple(image_df.columns)}",
    )

    _assert(
        photo_df.height == int(manifest_row_counts["total"]),
        "photo_metadata row count does not match row_counts.total",
    )
    _assert(
        image_df.height == int(manifest_row_counts["total"]),
        "image_path_manifest row count does not match row_counts.total",
    )

    status_counts = (
        image_df.group_by("image_status")
        .len()
        .rename({"len": "rows"})
        .to_dicts()
    )
    status_count_map: dict[str, int] = {}
    for row in status_counts:
        status = str(row["image_status"]) if row["image_status"] is not None else ""
        _assert(status in STATUS_CODES, f"Unexpected image_status in parquet: {status!r}")
        status_count_map[status] = int(row["rows"])

    for status in STATUS_CODES:
        _assert(
            status_count_map.get(status, 0) == int(manifest_row_counts[status]),
            f"row_counts[{status}] mismatch parquet count "
            f"({manifest_row_counts[status]} vs {status_count_map.get(status, 0)})",
        )

    reason_values = image_df.get_column("reason_code").drop_nulls().to_list()
    for reason in reason_values:
        if not reason:
            continue
        _assert(reason in REASON_CODES, f"Unexpected reason_code in parquet: {reason!r}")

    reason_counts = (
        image_df.filter(pl.col("reason_code") != "")
        .group_by("reason_code")
        .len()
        .rename({"len": "rows"})
        .to_dicts()
    )
    reason_count_map = {str(row["reason_code"]): int(row["rows"]) for row in reason_counts}
    for reason in REASON_CODES:
        _assert(
            reason_count_map.get(reason, 0) == int(manifest_integrity[reason]),
            f"integrity_counters[{reason}] mismatch parquet count "
            f"({manifest_integrity[reason]} vs {reason_count_map.get(reason, 0)})",
        )

    print(f"Photo-intake contract verification passed for {root}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify deterministic photo-intake contract artifacts.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("outputs/multimodal/photo_intake"),
        help="Artifact root directory (default: outputs/multimodal/photo_intake).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root
    if not root.is_absolute():
        root = (REPO_ROOT / root).resolve()

    try:
        verify(root)
    except VerificationError as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
