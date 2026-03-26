"""Contract tests for multimodal photo-intake artifact generation."""

from __future__ import annotations

import pytest

import polars as pl

from src.multimodal import photo_intake_contract as contract


def test_execute_photo_intake_contract_covers_status_and_reason_paths(tmp_path) -> None:
    """Contract execution should emit deterministic status/reason counters."""
    archive_dir = tmp_path / "photos"
    archive_dir.mkdir(parents=True)
    output_root = tmp_path / "out"
    metadata_path = tmp_path / "photos.json"

    # readable + labeled -> usable
    (archive_dir / "p1.jpg").write_bytes(b"\xff\xd8\xff")
    # readable + unlabeled -> linked
    (archive_dir / "p2.jpg").write_bytes(b"\xff\xd8\xff")
    # unreadable branch will be simulated via monkeypatch for p3
    (archive_dir / "p3.jpg").write_bytes(b"\xff\xd8\xff")

    rows = [
        {"photo_id": "p1", "business_id": "b1", "caption": "c1", "label": "food"},
        {"photo_id": "p2", "business_id": "b2", "caption": "c2", "label": ""},
        {"photo_id": "p3", "business_id": "b3", "caption": "c3", "label": "inside"},
        {"photo_id": "p_missing", "business_id": "b4", "caption": "c4", "label": "outside"},
        {"photo_id": "", "business_id": "", "caption": "bad", "label": "bad"},
    ]

    original_probe = contract._probe_readable

    def fake_probe(path):
        if str(path).endswith("p3.jpg"):
            return False
        return original_probe(path)

    from unittest.mock import patch

    with patch.object(contract, "_probe_readable", side_effect=fake_probe):
        result = contract.execute_photo_intake_contract(
            metadata_rows=rows,
            archive_dir=archive_dir,
            output_root=output_root,
            metadata_path=metadata_path,
        )

    assert result["row_counts"] == {
        "total": 5,
        "linked": 1,
        "missing": 2,
        "unreadable": 1,
        "usable": 1,
    }
    assert result["integrity_counters"] == {
        "archive_missing": 0,
        "metadata_missing_keys": 1,
        "image_file_missing": 1,
        "image_unreadable": 1,
    }


def test_execute_photo_intake_contract_counts_archive_missing(tmp_path) -> None:
    """When archive is absent, valid metadata rows should be reason-coded archive_missing."""
    output_root = tmp_path / "out"
    result = contract.execute_photo_intake_contract(
        metadata_rows=[{"photo_id": "p1", "business_id": "b1", "caption": "", "label": ""}],
        archive_dir=tmp_path / "does_not_exist",
        output_root=output_root,
        metadata_path=tmp_path / "photos.json",
    )

    assert result["row_counts"]["missing"] == 1
    assert result["integrity_counters"]["archive_missing"] == 1


def test_validate_contract_payload_rejects_column_drift() -> None:
    """Schema validation should fail fast when deterministic column order drifts."""
    photo_df = pl.DataFrame({"photo_id": [], "business_id": []})
    image_df = pl.DataFrame({"photo_id": [], "business_id": []})
    errors = contract.validate_contract_payload(
        photo_metadata_df=photo_df,
        image_manifest_df=image_df,
        row_counts={"total": 0, "linked": 0, "missing": 0, "unreadable": 0, "usable": 0},
        integrity_counters={reason: 0 for reason in contract.REASON_CODES},
    )
    assert any("columns mismatch" in error for error in errors)


def test_validate_contract_payload_rejects_invalid_status_vocab() -> None:
    """Unknown row status values should be flagged."""
    photo_df = pl.DataFrame({name: [] for name in contract.PHOTO_METADATA_COLUMNS})
    image_df = pl.DataFrame(
        {
            "photo_id": ["p1"],
            "business_id": ["b1"],
            "image_path": ["/tmp/p1.jpg"],
            "image_status": ["unknown_status"],
            "reason_code": [""],
        }
    )
    errors = contract.validate_contract_payload(
        photo_metadata_df=photo_df,
        image_manifest_df=image_df,
        row_counts={"total": 1, "linked": 0, "missing": 0, "unreadable": 0, "usable": 1},
        integrity_counters={reason: 0 for reason in contract.REASON_CODES},
    )
    assert any("invalid image_status values" in error for error in errors)


def test_validate_contract_payload_rejects_counter_key_drift() -> None:
    """Counter maps should enforce explicit, complete reason-code keys."""
    photo_df = pl.DataFrame({name: [] for name in contract.PHOTO_METADATA_COLUMNS})
    image_df = pl.DataFrame({name: [] for name in contract.IMAGE_PATH_MANIFEST_COLUMNS})
    errors = contract.validate_contract_payload(
        photo_metadata_df=photo_df,
        image_manifest_df=image_df,
        row_counts={"total": 0, "linked": 0, "missing": 0, "unreadable": 0, "usable": 0},
        integrity_counters={"archive_missing": 0},
    )
    assert any("integrity_counters keys mismatch" in error for error in errors)
