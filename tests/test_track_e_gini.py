"""Unit tests for Track E Stage 5 Gini helper functions."""

from __future__ import annotations

import numpy as np

from src.eda.track_e.imbalance_analysis import gini


def test_gini_equal_distribution_near_zero() -> None:
    values = np.array([1.0, 1.0, 1.0])
    assert abs(gini(values)) < 0.01


def test_gini_concentrated_distribution_high_value() -> None:
    values = np.array([0.0, 0.0, 0.0, 100.0])
    assert gini(values) > 0.7


def test_gini_bounds_always_between_zero_and_one() -> None:
    rng = np.random.default_rng(seed=0)
    for _ in range(5):
        values = rng.uniform(0, 100, size=10)
        result = gini(values)
        assert 0.0 <= result <= 1.0
