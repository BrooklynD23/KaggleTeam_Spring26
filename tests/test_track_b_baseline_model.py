"""Tests for Track B baseline helpers."""

import numpy as np

from src.modeling.track_b.baseline import ndcg_at_k, recall_at_k, split_name_for_group


def test_split_name_for_group_is_deterministic() -> None:
    group_key = 'business|abc|A: 0-90d'
    first = split_name_for_group(group_key)
    second = split_name_for_group(group_key)
    assert first == second
    assert first in {'train', 'validation', 'test'}


def test_ndcg_at_k_is_one_for_perfect_ordering() -> None:
    relevances = np.array([3.0, 2.0, 1.0])
    scores = np.array([0.9, 0.6, 0.1])
    assert ndcg_at_k(relevances, scores, k=3) == 1.0


def test_recall_at_k_handles_no_positives() -> None:
    labels = np.array([0, 0, 0])
    scores = np.array([0.2, 0.1, 0.3])
    assert recall_at_k(labels, scores, k=2) is None


def test_recall_at_k_counts_hits_in_top_k() -> None:
    labels = np.array([1, 0, 1, 0])
    scores = np.array([0.9, 0.1, 0.8, 0.2])
    assert recall_at_k(labels, scores, k=2) == 1.0
