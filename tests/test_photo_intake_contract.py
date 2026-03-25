"""Contract tests for multimodal photo intake normalization and integrity diagnostics."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.multimodal.photo_intake_contract import (
    IMAGE_PATH_MANIFEST_COLUMNS,
    INTEGRITY_COUNTER_KEYS,
    PHOTO_METADATA_COLUMNS,
    REASON_ARCHIVE_MISSING,
    REASON_IMAGE_FILE_MISSING,
    REASON_IMAGE_UNREADABLE,
    REASON_METADATA_MISSING_KEYS,
    STATUS_LINKED,
    STATUS_MISSING,
    STATUS_UNREADABLE,
    STATUS_USABLE,
    PhotoIntakeRecord,
    aggregate_integrity_counters,
    build_photo_intake_records,
    validate_columns,
    validate_integrity_counters_schema,
    validate_status_vocabulary,
)


def test_build_photo_intake_records_covers_integrity_branches(tmp_path: Path) -> None:
    """Contract rows should cover linked, missing, unreadable, and usable states."""
    image_root = tmp_path / "photos"
    image_root.mkdir(parents=True)

    usable_path = image_root / "p_usable.jpg"
    usable_path.write_bytes(b"ok-bytes")

    unreadable_path = image_root / "p_unreadable.jpg"
    unreadable_path.write_bytes(b"bad-bytes")

    rows = [
        {
            "photo_id": "p_missing_file",
            "business_id": "b_missing",
            "caption": "missing file",
            "label": "inside",
        },
        {
            "photo_id": "p_unreadable",
            "business_id": "b_unreadable",
            "caption": "unreadable file",
            "label": "outside",
        },
        {
            "photo_id": "p_usable",
            "business_id": "b_usable",
            "caption": "usable file",
            "label": "food",
        },
        {
            "photo_id": "p_missing_metadata",
            "caption": "missing metadata key",
            "label": "menu",
        },
    ]

    file_health_records = build_photo_intake_records(
        rows,
        image_root=image_root,
        archive_available=True,
        is_unreadable=lambda path: path.name == unreadable_path.name,
    )

    linked_records = build_photo_intake_records(
        [
            {
                "photo_id": "p_linked_only",
                "business_id": "b_linked",
                "caption": "archive absent",
                "label": "drink",
            }
        ],
        image_root=image_root,
        archive_available=False,
    )

    statuses = {record.photo_id: record.status for record in file_health_records + linked_records}
    reasons = {
        record.photo_id: record.reason_code
        for record in file_health_records + linked_records
    }

    assert statuses["p_linked_only"] == STATUS_LINKED
    assert statuses["p_missing_metadata"] == STATUS_MISSING
    assert statuses["p_missing_file"] == STATUS_MISSING
    assert statuses["p_unreadable"] == STATUS_UNREADABLE
    assert statuses["p_usable"] == STATUS_USABLE

    assert reasons["p_linked_only"] == REASON_ARCHIVE_MISSING
    assert reasons["p_missing_metadata"] == REASON_METADATA_MISSING_KEYS
    assert reasons["p_missing_file"] == REASON_IMAGE_FILE_MISSING
    assert reasons["p_unreadable"] == REASON_IMAGE_UNREADABLE
    assert reasons["p_usable"] == ""

    counters = aggregate_integrity_counters(file_health_records + linked_records)

    assert counters == {
        "photos_discovered": 5,
        "photos_linked": 1,
        "photos_missing": 2,
        "photos_unreadable": 1,
        "photos_usable": 1,
        REASON_ARCHIVE_MISSING: 1,
        REASON_METADATA_MISSING_KEYS: 1,
        REASON_IMAGE_FILE_MISSING: 1,
        REASON_IMAGE_UNREADABLE: 1,
    }


def test_build_photo_intake_records_is_deterministic_on_input_order(tmp_path: Path) -> None:
    """Rows should be emitted in deterministic order regardless of input order."""
    image_root = tmp_path / "photos"
    image_root.mkdir(parents=True)
    (image_root / "p2.jpg").write_bytes(b"bytes")
    (image_root / "p1.jpg").write_bytes(b"bytes")

    records = build_photo_intake_records(
        [
            {"photo_id": "p2", "business_id": "b2", "caption": "c2", "label": "l2"},
            {"photo_id": "p1", "business_id": "b1", "caption": "c1", "label": "l1"},
        ],
        image_root=image_root,
        archive_available=True,
    )

    assert [record.photo_id for record in records] == ["p1", "p2"]


def test_validate_columns_fails_on_schema_drift() -> None:
    """Schema validators should fail if key order or names drift."""
    with pytest.raises(ValueError, match="schema drift"):
        validate_columns(
            ("business_id", "photo_id", "caption", "label"),
            PHOTO_METADATA_COLUMNS,
            name="photo_metadata",
        )

    with pytest.raises(ValueError, match="schema drift"):
        validate_columns(
            IMAGE_PATH_MANIFEST_COLUMNS[:-1],
            IMAGE_PATH_MANIFEST_COLUMNS,
            name="image_path_manifest",
        )


def test_validate_status_vocabulary_fails_on_unknown_status() -> None:
    """Status validators must reject unknown status values."""
    records = [
        PhotoIntakeRecord(
            photo_id="p_bad",
            business_id="b_bad",
            caption="bad status",
            label="inside",
            image_path="/tmp/p_bad.jpg",
            status="broken",
            reason_code="",
        )
    ]

    with pytest.raises(ValueError, match="Invalid status"):
        validate_status_vocabulary(records)


def test_validate_integrity_counters_schema_fails_on_key_and_type_drift() -> None:
    """Counter validation should fail on missing keys and invalid counter types."""
    good = {key: 0 for key in INTEGRITY_COUNTER_KEYS}
    validate_integrity_counters_schema(good)

    bad_keys = dict(good)
    bad_keys.pop("photos_usable")
    with pytest.raises(ValueError, match="key drift"):
        validate_integrity_counters_schema(bad_keys)

    bad_type = dict(good)
    bad_type[REASON_IMAGE_UNREADABLE] = -1
    with pytest.raises(ValueError, match="non-negative int"):
        validate_integrity_counters_schema(bad_type)
