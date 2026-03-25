"""Deterministic contract helpers for Yelp photo intake artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

PHOTO_METADATA_COLUMNS: tuple[str, ...] = (
    "photo_id",
    "business_id",
    "caption",
    "label",
)

IMAGE_PATH_MANIFEST_COLUMNS: tuple[str, ...] = (
    "photo_id",
    "business_id",
    "caption",
    "label",
    "image_path",
    "status",
    "reason_code",
)

STATUS_LINKED = "linked"
STATUS_MISSING = "missing"
STATUS_UNREADABLE = "unreadable"
STATUS_USABLE = "usable"

STATUS_VOCABULARY: tuple[str, ...] = (
    STATUS_LINKED,
    STATUS_MISSING,
    STATUS_UNREADABLE,
    STATUS_USABLE,
)

REASON_ARCHIVE_MISSING = "archive_missing"
REASON_METADATA_MISSING_KEYS = "metadata_missing_keys"
REASON_IMAGE_FILE_MISSING = "image_file_missing"
REASON_IMAGE_UNREADABLE = "image_unreadable"

REASON_VOCABULARY: tuple[str, ...] = (
    REASON_ARCHIVE_MISSING,
    REASON_METADATA_MISSING_KEYS,
    REASON_IMAGE_FILE_MISSING,
    REASON_IMAGE_UNREADABLE,
)

INTEGRITY_COUNTER_KEYS: tuple[str, ...] = (
    "photos_discovered",
    "photos_linked",
    "photos_missing",
    "photos_unreadable",
    "photos_usable",
    REASON_ARCHIVE_MISSING,
    REASON_METADATA_MISSING_KEYS,
    REASON_IMAGE_FILE_MISSING,
    REASON_IMAGE_UNREADABLE,
)


@dataclass(frozen=True)
class NormalizedPhotoMetadata:
    """Normalized photo metadata row with deterministic key availability."""

    photo_id: str
    business_id: str
    caption: str
    label: str
    missing_keys: tuple[str, ...]


@dataclass(frozen=True)
class PhotoIntakeRecord:
    """Normalized and resolved photo intake row for contract artifacts."""

    photo_id: str
    business_id: str
    caption: str
    label: str
    image_path: str
    status: str
    reason_code: str


def _normalize_string(value: Any) -> str:
    """Convert a value to a deterministic string representation."""
    if value is None:
        return ""
    return str(value)


def normalize_photo_metadata_row(row: Mapping[str, Any]) -> NormalizedPhotoMetadata:
    """Normalize a raw metadata row into contract fields.

    Missing contract keys are tracked in ``missing_keys`` for integrity counting.
    """
    missing = tuple(sorted(key for key in PHOTO_METADATA_COLUMNS if key not in row))
    return NormalizedPhotoMetadata(
        photo_id=_normalize_string(row.get("photo_id")),
        business_id=_normalize_string(row.get("business_id")),
        caption=_normalize_string(row.get("caption")),
        label=_normalize_string(row.get("label")),
        missing_keys=missing,
    )


def resolve_image_path(
    photo_id: str,
    image_root: Path,
    *,
    image_extension: str = ".jpg",
) -> Path:
    """Resolve deterministic image path from photo ID."""
    extension = image_extension if image_extension.startswith(".") else f".{image_extension}"
    return image_root / f"{photo_id}{extension}"


def build_photo_intake_records(
    rows: Iterable[Mapping[str, Any]],
    image_root: Path,
    *,
    archive_available: bool,
    image_extension: str = ".jpg",
    is_unreadable: Callable[[Path], bool] | None = None,
) -> list[PhotoIntakeRecord]:
    """Build deterministic intake records covering linked/missing/unreadable/usable states."""
    unreadable_checker = is_unreadable or (lambda _path: False)
    records: list[PhotoIntakeRecord] = []

    normalized_rows = [normalize_photo_metadata_row(row) for row in rows]
    for normalized in sorted(
        normalized_rows,
        key=lambda item: (item.photo_id, item.business_id, item.caption, item.label),
    ):
        image_path = ""
        status = STATUS_MISSING
        reason_code = ""

        if normalized.missing_keys:
            reason_code = REASON_METADATA_MISSING_KEYS
        else:
            resolved_path = resolve_image_path(
                normalized.photo_id,
                image_root,
                image_extension=image_extension,
            )
            image_path = str(resolved_path)

            if not archive_available:
                status = STATUS_LINKED
                reason_code = REASON_ARCHIVE_MISSING
            elif not resolved_path.is_file():
                status = STATUS_MISSING
                reason_code = REASON_IMAGE_FILE_MISSING
            elif unreadable_checker(resolved_path):
                status = STATUS_UNREADABLE
                reason_code = REASON_IMAGE_UNREADABLE
            else:
                status = STATUS_USABLE

        records.append(
            PhotoIntakeRecord(
                photo_id=normalized.photo_id,
                business_id=normalized.business_id,
                caption=normalized.caption,
                label=normalized.label,
                image_path=image_path,
                status=status,
                reason_code=reason_code,
            )
        )

    return records


def aggregate_integrity_counters(records: Sequence[PhotoIntakeRecord]) -> dict[str, int]:
    """Aggregate deterministic integrity counters for manifest/report surfaces."""
    counters = {key: 0 for key in INTEGRITY_COUNTER_KEYS}
    counters["photos_discovered"] = len(records)

    for record in records:
        if record.status == STATUS_LINKED:
            counters["photos_linked"] += 1
        elif record.status == STATUS_MISSING:
            counters["photos_missing"] += 1
        elif record.status == STATUS_UNREADABLE:
            counters["photos_unreadable"] += 1
        elif record.status == STATUS_USABLE:
            counters["photos_usable"] += 1
        else:
            raise ValueError(f"Unknown status in record: {record.status}")

        if record.reason_code:
            if record.reason_code not in REASON_VOCABULARY:
                raise ValueError(f"Unknown reason code in record: {record.reason_code}")
            counters[record.reason_code] += 1

    return counters


def validate_columns(columns: Iterable[str], expected: Sequence[str], *, name: str) -> None:
    """Validate a deterministic schema surface by exact column set and order."""
    observed = tuple(columns)
    expected_tuple = tuple(expected)
    if observed != expected_tuple:
        raise ValueError(
            f"{name} schema drift detected: expected {expected_tuple}, observed {observed}"
        )


def validate_status_vocabulary(records: Sequence[PhotoIntakeRecord]) -> None:
    """Fail fast on status/reason vocabulary drift in intake records."""
    allowed_statuses = set(STATUS_VOCABULARY)
    allowed_reasons = set(REASON_VOCABULARY)

    for record in records:
        if record.status not in allowed_statuses:
            raise ValueError(f"Invalid status '{record.status}' for photo_id={record.photo_id}")
        if record.reason_code and record.reason_code not in allowed_reasons:
            raise ValueError(
                f"Invalid reason_code '{record.reason_code}' for photo_id={record.photo_id}"
            )


def validate_integrity_counters_schema(counters: Mapping[str, Any]) -> None:
    """Validate machine-readable integrity counters for key/type drift."""
    observed_keys = tuple(counters.keys())
    if observed_keys != INTEGRITY_COUNTER_KEYS:
        raise ValueError(
            "Integrity counter key drift detected: "
            f"expected {INTEGRITY_COUNTER_KEYS}, observed {observed_keys}"
        )

    for key in INTEGRITY_COUNTER_KEYS:
        value = counters[key]
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"Integrity counter '{key}' must be a non-negative int, got {value!r}"
            )
