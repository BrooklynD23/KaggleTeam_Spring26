"""Pre-ingestion JSON structure validation for Yelp dataset entities."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ENTITY_CONFIGS: dict[str, list[str]] = {
    "business": [
        "business_id", "name", "address", "city", "state",
        "postal_code", "latitude", "longitude", "stars",
        "review_count", "is_open", "attributes", "categories", "hours",
    ],
    "review": [
        "review_id", "user_id", "business_id", "stars", "date",
        "text", "useful", "funny", "cool",
    ],
    "user": [
        "user_id", "name", "review_count", "yelping_since",
        "useful", "funny", "cool", "elite", "friends", "fans",
        "average_stars", "compliment_hot", "compliment_more",
        "compliment_profile", "compliment_cute", "compliment_list",
        "compliment_note", "compliment_plain", "compliment_cool",
        "compliment_funny", "compliment_writer", "compliment_photos",
    ],
    "tip": [
        "user_id", "business_id", "text", "date", "compliment_count",
    ],
    "checkin": [
        "business_id", "date",
    ],
}


def validate_first_n_lines(
    filepath: str | Path,
    entity: str,
    n: int = 100,
) -> dict[str, Any]:
    """Validate that the first N lines of an NDJSON file contain required keys.

    Args:
        filepath: Path to the NDJSON file.
        entity: Entity name (must be a key in ENTITY_CONFIGS).
        n: Number of lines to validate.

    Returns:
        A dict with entity, lines_checked, missing_key_issues,
        extra_keys_observed, and status.

    Raises:
        ValueError: If entity is not recognised.
        FileNotFoundError: If filepath does not exist.
    """
    if entity not in ENTITY_CONFIGS:
        raise ValueError(
            f"Unknown entity '{entity}'. "
            f"Valid entities: {list(ENTITY_CONFIGS.keys())}"
        )

    filepath = Path(filepath)
    if not filepath.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")

    required_keys = set(ENTITY_CONFIGS[entity])
    missing_key_issues: list[dict[str, Any]] = []
    extra_keys_observed: set[str] = set()
    lines_checked = 0

    with open(filepath, "r", encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            if line_num > n:
                break
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                missing_key_issues.append({
                    "line": line_num,
                    "error": f"Invalid JSON: {exc}",
                })
                lines_checked += 1
                continue

            record_keys = set(record.keys())
            missing = required_keys - record_keys
            extra = record_keys - required_keys

            if missing:
                missing_key_issues.append({
                    "line": line_num,
                    "missing_keys": sorted(missing),
                })

            extra_keys_observed.update(extra)
            lines_checked += 1

    status = "FAIL" if missing_key_issues else "PASS"

    logger.info(
        "Validation %s for entity '%s': checked %d lines, %d issues",
        status, entity, lines_checked, len(missing_key_issues),
    )

    return {
        "entity": entity,
        "lines_checked": lines_checked,
        "missing_key_issues": missing_key_issues,
        "extra_keys_observed": sorted(extra_keys_observed),
        "status": status,
    }
