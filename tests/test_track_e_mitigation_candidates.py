"""Regression tests for Track E Stage 8 mitigation report priorities."""

from __future__ import annotations

import pandas as pd

from src.eda.track_e.mitigation_candidates import build_mitigation_report


def _config() -> dict[str, object]:
    return {
        "fairness": {
            "demographic_parity_threshold": 0.1,
            "coverage_parity_min_ratio": 0.5,
        }
    }


def _priority_lines(report: str) -> list[str]:
    lines = report.splitlines()
    in_priority = False
    collected: list[str] = []
    for line in lines:
        if line == "## 5. Recommended Priority":
            in_priority = True
            continue
        if in_priority and line.startswith("## "):
            break
        if in_priority and line.startswith("- "):
            collected.append(line)
    return collected


def test_coverage_priority_uses_ratio_shortfall_not_gap_units() -> None:
    fairness_df = pd.DataFrame(
        [
            {
                "subgroup_type": "city",
                "metric_name": "coverage_parity_ratio",
                "group_a": "Phoenix",
                "group_b": "Vegas",
                "group_a_value": 100.0,
                "group_b_value": 20.0,
                "gap": 80.0,
                "ratio": 0.2,
                "exceeds_threshold": True,
            }
        ]
    )

    report = build_mitigation_report(
        fairness_df=fairness_df,
        proxy_df=pd.DataFrame(),
        imbalance_df=pd.DataFrame(),
        config=_config(),
    )
    priority_lines = _priority_lines(report)
    assert any("falls below minimum ratio by 0.30" in line for line in priority_lines)
    assert any("(ratio=0.20, min=0.5)." in line for line in priority_lines)
    assert not any("gap=80.00" in line for line in priority_lines)


def test_coverage_priority_sorts_by_ratio_shortfall_not_raw_gap() -> None:
    fairness_df = pd.DataFrame(
        [
            {
                "subgroup_type": "city",
                "metric_name": "coverage_parity_ratio",
                "group_a": "A",
                "group_b": "B",
                "group_a_value": 1000.0,
                "group_b_value": 490.0,
                "gap": 510.0,
                "ratio": 0.49,
                "exceeds_threshold": True,
            },
            {
                "subgroup_type": "price_tier",
                "metric_name": "coverage_parity_ratio",
                "group_a": "high",
                "group_b": "low",
                "group_a_value": 100.0,
                "group_b_value": 10.0,
                "gap": 90.0,
                "ratio": 0.10,
                "exceeds_threshold": True,
            },
        ]
    )

    report = build_mitigation_report(
        fairness_df=fairness_df,
        proxy_df=pd.DataFrame(),
        imbalance_df=pd.DataFrame(),
        config=_config(),
    )
    priority_lines = _priority_lines(report)
    coverage_lines = [line for line in priority_lines if "coverage_parity_ratio" in line]
    assert len(coverage_lines) == 2
    assert "price_tier" in coverage_lines[0]
