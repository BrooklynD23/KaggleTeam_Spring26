"""Shared domain helpers reusable across multiple tracks."""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def primary_category(value: Any) -> str | None:
    """Extract the first category token from a Yelp comma-separated categories string.

    >>> primary_category("Restaurants, Mexican, Bars")
    'Restaurants'
    >>> primary_category(None)
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.split(",")[0].strip() or None


def parse_jsonish(raw: Any) -> dict[str, Any]:
    """Parse a JSON-ish string from Yelp's attributes/hours fields.

    Yelp encodes some fields as Python repr strings (single quotes, None, True/False)
    rather than valid JSON. This function tries multiple transformations.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return {}
    if isinstance(raw, dict):
        return raw

    text = str(raw).strip()
    if not text or text.lower() in {"null", "none"}:
        return {}

    candidates = [
        text,
        text.replace("'", '"'),
        text.replace("None", "null").replace("True", "true").replace("False", "false"),
        text.replace("'", '"').replace("None", "null").replace("True", "true").replace("False", "false"),
    ]
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def extract_price_range(attributes_raw: Any) -> int | None:
    """Extract RestaurantsPriceRange2 when present.

    Returns an integer 1-4, or None if the field is missing or unparseable.
    Only restaurant businesses have this attribute; expect >= 30% null rate
    across all businesses.
    """
    attributes = parse_jsonish(attributes_raw)
    value = attributes.get("RestaurantsPriceRange2")
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip('"')
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
