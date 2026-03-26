"""Runtime tests for multimodal photo-intake CLI wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.multimodal import photo_intake as runtime


def test_load_photo_metadata_rows_parses_ndjson_and_skips_blank_lines(tmp_path: Path) -> None:
    """NDJSON metadata loader should parse object rows and ignore blanks."""
    metadata_path = tmp_path / "photos.json"
    metadata_path.write_text(
        "\n".join(
            [
                json.dumps({"photo_id": "p1", "business_id": "b1"}),
                "",
                "  ",
                json.dumps({"photo_id": "p2", "business_id": "b2", "label": "food"}),
            ]
        ),
        encoding="utf-8",
    )

    rows = runtime._load_photo_metadata_rows(metadata_path)

    assert len(rows) == 2
    assert rows[0]["photo_id"] == "p1"
    assert rows[1]["photo_id"] == "p2"


def test_load_photo_metadata_rows_rejects_invalid_json(tmp_path: Path) -> None:
    """Metadata loader should fail with line-number context for bad JSON."""
    metadata_path = tmp_path / "photos.json"
    metadata_path.write_text('{"photo_id": "p1"}\n{"photo_id": invalid}\n', encoding="utf-8")

    with pytest.raises(runtime.PhotoIntakeRuntimeError, match="line 2"):
        runtime._load_photo_metadata_rows(metadata_path)


def test_load_photo_metadata_rows_rejects_non_object_rows(tmp_path: Path) -> None:
    """Metadata loader should reject non-dict JSON rows."""
    metadata_path = tmp_path / "photos.json"
    metadata_path.write_text('["not", "an", "object"]\n', encoding="utf-8")

    with pytest.raises(runtime.PhotoIntakeRuntimeError, match="Expected object rows"):
        runtime._load_photo_metadata_rows(metadata_path)


def test_run_executes_contract_and_writes_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Runtime should resolve configured paths from PROJECT_ROOT and emit contract artifacts."""
    metadata_dir = tmp_path / "data" / "raw"
    archive_dir = metadata_dir / "photos"
    output_root = tmp_path / "outputs" / "multimodal" / "photo_intake"

    archive_dir.mkdir(parents=True)
    (archive_dir / "p1.jpg").write_bytes(b"\xff\xd8\xff")

    metadata_path = metadata_dir / "photos.json"
    metadata_path.write_text(
        json.dumps({
            "photo_id": "p1",
            "business_id": "b1",
            "caption": "test",
            "label": "food",
        })
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(runtime, "PROJECT_ROOT", tmp_path)

    result = runtime.run(
        {
            "multimodal": {
                "photo_intake": {
                    "metadata_path": "data/raw/photos.json",
                    "archive_dir": "data/raw/photos",
                    "output_root": "outputs/multimodal/photo_intake",
                }
            }
        }
    )

    assert result["row_counts"] == {
        "total": 1,
        "linked": 0,
        "missing": 0,
        "unreadable": 0,
        "usable": 1,
    }
    assert (output_root / "manifest.json").is_file()
    assert (output_root / "validation_report.json").is_file()
    assert (output_root / "photo_metadata.parquet").is_file()
    assert (output_root / "image_path_manifest.parquet").is_file()


def test_run_requires_config_block_and_paths() -> None:
    """Runtime should fail fast when required photo_intake keys are missing."""
    with pytest.raises(runtime.PhotoIntakeRuntimeError, match="must define"):
        runtime.run({"multimodal": {"photo_intake": {"metadata_path": "x"}}})
