"""Regression tests for shared helpers promoted from Track D."""

from __future__ import annotations

from src.common import helpers as common_helpers
from src.eda.track_d import common as track_d_common


def test_promoted_helpers_preserve_expected_behavior() -> None:
    """Shared helper behavior should match the promoted Track D contract."""
    assert common_helpers.primary_category("Restaurants, Mexican, Bars") == "Restaurants"
    assert common_helpers.primary_category(None) is None
    assert common_helpers.parse_jsonish("{'A': '1', 'B': None}") == {"A": "1", "B": None}
    assert common_helpers.extract_price_range('{"RestaurantsPriceRange2": "3"}') == 3


def test_track_d_re_exports_point_to_promoted_helpers() -> None:
    """Track D should re-export the promoted helper functions directly."""
    assert track_d_common.primary_category is common_helpers.primary_category
    assert track_d_common.parse_jsonish is common_helpers.parse_jsonish
    assert track_d_common.extract_price_range is common_helpers.extract_price_range
