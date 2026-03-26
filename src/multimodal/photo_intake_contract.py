"""Deterministic contract builder for Yelp photo intake artifacts."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)

STATUS_CODES: tuple[str, ...] = ("linked", "missing", "unreadable", "usable")
REASON_CODES: tuple[str, ...] = (
    "archive_missing",
    "metadata_missing_keys",
    "image_file_missing",
    "image_unreadable",
)

PHOTO_METADATA_COLUMNS: tuple[str, ...] = (
    "photo_id",
    "business_id",
    "caption",
    "label",
)
IMAGE_PATH_MANIFEST_COLUMNS: tuple[str, ...] = (
    "photo_id",
    "business_id",
    "image_path",
    "image_status",
    "reason_code",
)

REQUIRED_METADATA_KEYS: tuple[str, ...] = ("photo_id", "business_id")


class PhotoIntakeContractError(RuntimeError):
    """Raised when a photo-intake contract artifact fails validation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _to_clean_string(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return text


def normalize_metadata_row(raw: dict[str, Any]) -> dict[str, str]:
    """Normalize one raw metadata row into canonical contract keys."""
    return {
        "photo_id": _to_clean_string(raw.get("photo_id")),
        "business_id": _to_clean_string(raw.get("business_id")),
        "caption": _to_clean_string(raw.get("caption")),
        "label": _to_clean_string(raw.get("label")),
    }


def _default_image_path(archive_dir: Path, photo_id: str) -> Path:
    return archive_dir / f"{photo_id}.jpg"


def _probe_readable(path: Path) -> bool:
    try:
        with open(path, "rb") as handle:
            _ = handle.read(1)
        return True
    except OSError:
        return False


def _empty_dataframe(columns: tuple[str, ...]) -> pl.DataFrame:
    return pl.DataFrame({name: pl.Series(name, [], dtype=pl.String) for name in columns})


def _rows_to_df(rows: list[dict[str, str]], columns: tuple[str, ...]) -> pl.DataFrame:
    if not rows:
        return _empty_dataframe(columns)
    return pl.DataFrame(rows).select(list(columns))


def validate_contract_payload(
    photo_metadata_df: pl.DataFrame,
    image_manifest_df: pl.DataFrame,
    row_counts: dict[str, int],
    integrity_counters: dict[str, int],
) -> list[str]:
    """Validate deterministic schema and vocabulary expectations."""
    errors: list[str] = []

    if tuple(photo_metadata_df.columns) != PHOTO_METADATA_COLUMNS:
        errors.append(
            "photo_metadata columns mismatch: "
            f"expected {PHOTO_METADATA_COLUMNS}, got {tuple(photo_metadata_df.columns)}"
        )

    if tuple(image_manifest_df.columns) != IMAGE_PATH_MANIFEST_COLUMNS:
        errors.append(
            "image_path_manifest columns mismatch: "
            f"expected {IMAGE_PATH_MANIFEST_COLUMNS}, got {tuple(image_manifest_df.columns)}"
        )

    status_values = set(
        image_manifest_df.get_column("image_status").drop_nulls().to_list()
        if "image_status" in image_manifest_df.columns
        else []
    )
    invalid_statuses = sorted(status for status in status_values if status not in STATUS_CODES)
    if invalid_statuses:
        errors.append(f"invalid image_status values: {invalid_statuses}")

    reason_values = set(
        image_manifest_df.get_column("reason_code").drop_nulls().to_list()
        if "reason_code" in image_manifest_df.columns
        else []
    )
    invalid_reasons = sorted(reason for reason in reason_values if reason and reason not in REASON_CODES)
    if invalid_reasons:
        errors.append(f"invalid reason_code values: {invalid_reasons}")

    expected_row_keys = {"total", *STATUS_CODES}
    if set(row_counts.keys()) != expected_row_keys:
        errors.append(
            "row_counts keys mismatch: "
            f"expected {sorted(expected_row_keys)}, got {sorted(row_counts.keys())}"
        )

    if set(integrity_counters.keys()) != set(REASON_CODES):
        errors.append(
            "integrity_counters keys mismatch: "
            f"expected {sorted(REASON_CODES)}, got {sorted(integrity_counters.keys())}"
        )

    return errors


def execute_photo_intake_contract(
    metadata_rows: list[dict[str, Any]],
    archive_dir: Path,
    output_root: Path,
    metadata_path: Path,
) -> dict[str, Any]:
    """Build and persist deterministic photo-intake contract artifacts."""
    output_root.mkdir(parents=True, exist_ok=True)

    archive_exists = archive_dir.is_dir()
    normalized_rows = [normalize_metadata_row(row) for row in metadata_rows]

    image_manifest_rows: list[dict[str, str]] = []
    row_counts: dict[str, int] = {"total": 0, "linked": 0, "missing": 0, "unreadable": 0, "usable": 0}
    integrity_counters: dict[str, int] = {reason: 0 for reason in REASON_CODES}

    for row in normalized_rows:
        row_counts["total"] += 1
        photo_id = row["photo_id"]
        business_id = row["business_id"]

        reason_code = ""
        image_status = "linked"
        image_path = ""

        missing_required = [key for key in REQUIRED_METADATA_KEYS if not row[key]]
        if missing_required:
            image_status = "missing"
            reason_code = "metadata_missing_keys"
            integrity_counters[reason_code] += 1
        else:
            candidate_path = _default_image_path(archive_dir, photo_id)
            image_path = str(candidate_path)
            if not archive_exists:
                image_status = "missing"
                reason_code = "archive_missing"
                integrity_counters[reason_code] += 1
            elif not candidate_path.is_file():
                image_status = "missing"
                reason_code = "image_file_missing"
                integrity_counters[reason_code] += 1
            elif not _probe_readable(candidate_path):
                image_status = "unreadable"
                reason_code = "image_unreadable"
                integrity_counters[reason_code] += 1
            elif row["label"]:
                image_status = "usable"
            else:
                image_status = "linked"

        row_counts[image_status] += 1
        image_manifest_rows.append(
            {
                "photo_id": photo_id,
                "business_id": business_id,
                "image_path": image_path,
                "image_status": image_status,
                "reason_code": reason_code,
            }
        )

    photo_metadata_df = _rows_to_df(normalized_rows, PHOTO_METADATA_COLUMNS)
    image_manifest_df = _rows_to_df(image_manifest_rows, IMAGE_PATH_MANIFEST_COLUMNS)

    contract_errors = validate_contract_payload(
        photo_metadata_df=photo_metadata_df,
        image_manifest_df=image_manifest_df,
        row_counts=row_counts,
        integrity_counters=integrity_counters,
    )

    manifest = {
        "schema_version": "1.0",
        "created_at": _utc_now_iso(),
        "inputs": {
            "metadata_path": str(metadata_path),
            "archive_dir": str(archive_dir),
            "archive_exists": archive_exists,
            "metadata_rows": len(normalized_rows),
        },
        "phases": {
            "metadata_load": {"status": "ok"},
            "path_resolution": {"status": "ok" if not contract_errors else "failed"},
        },
        "row_counts": row_counts,
        "integrity_counters": integrity_counters,
        "artifacts": {
            "photo_metadata_parquet": str(output_root / "photo_metadata.parquet"),
            "image_path_manifest_parquet": str(output_root / "image_path_manifest.parquet"),
            "validation_report_json": str(output_root / "validation_report.json"),
        },
    }

    validation_report = {
        "status": "pass" if not contract_errors else "fail",
        "errors": contract_errors,
        "required_columns": {
            "photo_metadata": list(PHOTO_METADATA_COLUMNS),
            "image_path_manifest": list(IMAGE_PATH_MANIFEST_COLUMNS),
        },
        "allowed_statuses": list(STATUS_CODES),
        "allowed_reason_codes": list(REASON_CODES),
        "row_counts": row_counts,
        "integrity_counters": integrity_counters,
    }

    photo_metadata_path = output_root / "photo_metadata.parquet"
    image_manifest_path = output_root / "image_path_manifest.parquet"
    manifest_path = output_root / "manifest.json"
    validation_path = output_root / "validation_report.json"

    photo_metadata_df.write_parquet(photo_metadata_path)
    image_manifest_df.write_parquet(image_manifest_path)

    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")

    with open(validation_path, "w", encoding="utf-8") as handle:
        json.dump(validation_report, handle, indent=2, sort_keys=True)
        handle.write("\n")

    if contract_errors:
        logger.error("Photo-intake contract validation failed: %s", "; ".join(contract_errors))
        raise PhotoIntakeContractError(
            "Photo-intake contract validation failed: " + "; ".join(contract_errors)
        )

    logger.info("Photo-intake contract artifacts written to %s", output_root)
    return {
        "manifest_path": manifest_path,
        "validation_report_path": validation_path,
        "photo_metadata_path": photo_metadata_path,
        "image_path_manifest_path": image_manifest_path,
        "row_counts": row_counts,
        "integrity_counters": integrity_counters,
    }
