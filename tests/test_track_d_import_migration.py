"""Regression tests for Track D helper import migration."""

from __future__ import annotations

from src.common.helpers import extract_price_range, parse_jsonish, primary_category
from src.eda.track_d.common import (
    extract_price_range as track_d_extract_price_range,
    parse_jsonish as track_d_parse_jsonish,
    primary_category as track_d_primary_category,
)


def test_track_d_helper_re_exports_behave_identically() -> None:
    """Track D should expose the same helper behavior after promotion."""
    sample = "{'RestaurantsPriceRange2': '2', 'OutdoorSeating': True}"

    assert track_d_primary_category("Food, Grocery") == primary_category("Food, Grocery")
    assert track_d_parse_jsonish(sample) == parse_jsonish(sample)
    assert track_d_extract_price_range(sample) == extract_price_range(sample)
