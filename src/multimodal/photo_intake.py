"""CLI runtime for deterministic Yelp photo-intake contract artifacts."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from src.common.config import load_config
from src.multimodal.photo_intake_contract import execute_photo_intake_contract

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "multimodal.yaml"


class PhotoIntakeRuntimeError(RuntimeError):
    """Raised when intake runtime configuration is invalid."""


def _load_photo_metadata_rows(metadata_path: Path) -> list[dict[str, Any]]:
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Photo metadata file not found: {metadata_path}")

    rows: list[dict[str, Any]] = []
    with open(metadata_path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise PhotoIntakeRuntimeError(
                    f"Invalid JSON in {metadata_path} at line {line_number}."
                ) from exc
            if not isinstance(payload, dict):
                raise PhotoIntakeRuntimeError(
                    f"Expected object rows in {metadata_path} at line {line_number}."
                )
            rows.append(payload)
    return rows


def run(config: dict[str, Any]) -> dict[str, Any]:
    photo_cfg = config.get("multimodal", {}).get("photo_intake", {})
    if not isinstance(photo_cfg, dict):
        raise PhotoIntakeRuntimeError("Missing multimodal.photo_intake configuration block.")

    metadata_rel = photo_cfg.get("metadata_path")
    archive_rel = photo_cfg.get("archive_dir")
    output_rel = photo_cfg.get("output_root")
    if not metadata_rel or not archive_rel or not output_rel:
        raise PhotoIntakeRuntimeError(
            "multimodal.photo_intake must define metadata_path, archive_dir, and output_root."
        )

    metadata_path = PROJECT_ROOT / str(metadata_rel)
    archive_dir = PROJECT_ROOT / str(archive_rel)
    output_root = PROJECT_ROOT / str(output_rel)

    metadata_rows = _load_photo_metadata_rows(metadata_path)
    result = execute_photo_intake_contract(
        metadata_rows=metadata_rows,
        archive_dir=archive_dir,
        output_root=output_root,
        metadata_path=metadata_path,
    )

    logger.info(
        "Photo intake complete: total=%d usable=%d missing=%d unreadable=%d",
        result["row_counts"]["total"],
        result["row_counts"]["usable"],
        result["row_counts"]["missing"],
        result["row_counts"]["unreadable"],
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build deterministic multimodal photo-intake artifacts.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to YAML config file (default: configs/multimodal.yaml).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    log_level = str(config.get("log_level", "INFO")).upper()
    logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))

    run(config)


if __name__ == "__main__":
    main()
