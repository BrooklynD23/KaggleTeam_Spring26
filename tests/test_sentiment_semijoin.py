"""Regression: compute_sentiment must semijoin against review_fact review_ids."""

import inspect
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest


def test_compute_sentiment_accepts_review_fact_path() -> None:
    """compute_sentiment signature must include review_fact_path parameter."""
    from src.eda.track_a.text_profile import compute_sentiment

    sig = inspect.signature(compute_sentiment)
    assert "review_fact_path" in sig.parameters, (
        "compute_sentiment must accept 'review_fact_path' for the data-governance semijoin."
    )


def test_compute_sentiment_sql_uses_second_param(tmp_path: Path) -> None:
    """compute_sentiment must pass review_fact_path as a second SQL parameter ($2)."""
    executed_sqls: list[str] = []
    executed_params: list[list] = []

    empty_df = pd.DataFrame(columns=["review_id", "review_stars", "review_text"])
    mock_result = MagicMock()
    mock_result.fetchdf.return_value = empty_df

    mock_con = MagicMock()

    def side_effect(sql: str, params=None) -> MagicMock:
        executed_sqls.append(sql)
        executed_params.append(params or [])
        return mock_result

    mock_con.execute.side_effect = side_effect

    review_path = tmp_path / "review.parquet"
    review_path.touch()
    review_fact_path = tmp_path / "review_fact.parquet"
    review_fact_path.touch()

    # Patch TextBlob import so we don't need the dependency installed
    import sys
    from types import ModuleType
    from unittest.mock import patch

    fake_tb_module = ModuleType("textblob")

    class FakeTextBlob:
        def __init__(self, text: str) -> None:
            self.sentiment = MagicMock(polarity=0.5)

    fake_tb_module.TextBlob = FakeTextBlob  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"textblob": fake_tb_module}):
        from src.eda.track_a.text_profile import compute_sentiment

        compute_sentiment(mock_con, review_path, review_fact_path, {}, tmp_path)

    # The SQL should reference $2 (review_fact_path) or pass two parameters
    assert any(
        ("$2" in sql or len(params) >= 2) for sql, params in zip(executed_sqls, executed_params)
    ), (
        "compute_sentiment SQL must use review_fact_path as a second parameter "
        "to enforce the data-governance semijoin."
    )
