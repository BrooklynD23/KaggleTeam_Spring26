"""Stage 8 — Mitigation candidates for Track E."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import load_config
from src.eda.track_e.common import ensure_output_dirs, resolve_paths

logger = logging.getLogger(__name__)


def _load_table(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_parquet(path)
    logger.debug("Missing artifact %s — using empty frame", path)
    return pd.DataFrame()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _priority_score(row: pd.Series, dp_threshold: float, coverage_threshold: float) -> float:
    metric_name = str(row.get("metric_name", ""))
    if metric_name == "coverage_parity_ratio":
        ratio = _to_float(row.get("ratio"), default=1.0)
        return max(0.0, coverage_threshold - ratio)
    gap = _to_float(row.get("gap"))
    return max(0.0, gap - dp_threshold)


def _format_priority_line(row: pd.Series, dp_threshold: float, coverage_threshold: float) -> str:
    metric_name = str(row.get("metric_name", ""))
    subgroup_type = str(row.get("subgroup_type", "unknown"))
    if metric_name == "coverage_parity_ratio":
        ratio = _to_float(row.get("ratio"), default=1.0)
        shortfall = max(0.0, coverage_threshold - ratio)
        return (
            f"- {metric_name} for {subgroup_type} falls below minimum ratio by {shortfall:.2f} "
            f"(ratio={ratio:.2f}, min={coverage_threshold})."
        )
    gap = _to_float(row.get("gap"))
    threshold_excess = max(0.0, gap - dp_threshold)
    return (
        f"- {metric_name} for {subgroup_type} exceeds gap threshold by {threshold_excess:.2f} "
        f"(gap={gap:.2f}, max={dp_threshold})."
    )


def build_mitigation_report(
    fairness_df: pd.DataFrame,
    proxy_df: pd.DataFrame,
    imbalance_df: pd.DataFrame,
    config: dict[str, Any],
) -> str:
    """Build the markdown report describing mitigation candidates."""
    fairness_cfg = config.get("fairness", {})
    dp_threshold = float(fairness_cfg.get("demographic_parity_threshold", 0.1))
    coverage_threshold = float(fairness_cfg.get("coverage_parity_min_ratio", 0.5))

    lines: list[str] = []
    lines.append("# Track E: Mitigation Candidates for Fairness-Aware Modeling")
    lines.append("## 1. Data-Level Mitigations")

    if "metric" in imbalance_df.columns:
        review_gini = imbalance_df.loc[imbalance_df["metric"] == "review_count"].copy()
    else:
        review_gini = pd.DataFrame()
    lines.append("### 1.1 Resampling")
    if not review_gini.empty:
        worst = review_gini.loc[review_gini["gini_coefficient"].idxmax()]
        lines.append(
            "- Strategy: If modeling downstream shows the same subgroup imbalance, consider oversampling underrepresented "
            f"values of {worst['subgroup_type']} to reflect the observed concentration (Gini={worst['gini_coefficient']:.2f}) "
            "while keeping reporting aggregate-only."
        )
        lines.append(
            "- Evidence: Stage 5 reports the concentration via track_e_s5_imbalance_report.parquet."
        )
    else:
        lines.append("- Strategy: Consider resampling rare subgroups once Stage 5 outputs are available.")
        lines.append("- Evidence: track_e_s5_imbalance_report.parquet will surface the relevant Gini scores.")

    lines.append("### 1.2 Reweighting")
    lines.append(
        "- Strategy: Apply higher sample weights to low-review-count subgroups instead of duplicating rows so the raw dataset "
        "distribution remains unchanged."
    )
    lines.append(
        "- Evidence: Stage 2 coverage_by_subgroup.parquet reports review counts for each subgroup; gaps there suggest this mitigation."
    )

    lines.append("## 2. Feature-Level Mitigations")
    lines.append("### 2.1 Proxy Feature Exclusion")

    if "is_proxy_risk" in proxy_df.columns:
        proxy_candidates = proxy_df.loc[proxy_df["is_proxy_risk"]].copy()
    else:
        proxy_candidates = pd.DataFrame()
    if proxy_candidates.empty:
        lines.append(
            "- Stage 6 did not flag proxy risks (`is_proxy_risk=True`). Re-run track_e_s6_proxy_correlations.parquet if new "
            "features are added."
        )
    else:
        lines.append(
            "- Strategy: Drop the following proxy-risk features or subject them to strong regularization when those subgroup indicators appear."
        )
        lines.append(
            "- Evidence: The rows below come from track_e_s6_proxy_correlations.parquet."
        )
        for row in proxy_candidates.itertuples(index=False):
            value = (
                f"(r={row.correlation:.2f}, p={row.p_value:.3f})"
                if hasattr(row, "correlation")
                else "(correlation not available)"
            )
            lines.append(
                f"- `{row.feature}` correlates with `{row.subgroup_indicator}` {value}; consider excluding or regularizing it."
            )

    lines.append("### 2.2 Feature Regularization")
    lines.append(
        "- Strategy: Apply higher penalties (L1 or structured regularization) to features flagged above so their weights shrink when disparities emerge."
    )
    lines.append(
        "- Evidence: Pair this with Stage 7 fairness metrics and Stage 6 proxy correlations to justify targeted coefficients."
    )

    lines.append("## 3. Model-Level Mitigations")
    lines.append("### 3.1 Fairness Constraints (Equalized Odds)")
    lines.append(
        "- Strategy: Introduce fairness-aware constraints, such as equalized odds or relaxed demographic parity, when models exhibit the same gaps documented in Stage 7."
    )
    lines.append(
        "- Evidence: Stage 7 fairness metrics are served from track_e_s7_fairness_metrics.parquet."
    )
    lines.append("### 3.2 Post-hoc Calibration")
    lines.append(
        "- Strategy: Perform per-subgroup calibration to align predicted distributions with the baseline gaps if calibration_gap rows are non-zero."
    )
    lines.append(
        "- Evidence: track_e_s7_fairness_metrics.parquet identifies the largest KS statistic per dimension."
    )

    lines.append("## 4. Reporting-Level Mitigations")
    lines.append("### 4.1 Aggregate-Only Reporting")
    lines.append(
        "- Strategy: Only disclose aggregates, enforce min_group_size from config.subgroups, and avoid implying individual-level causes."
    )
    lines.append(
        "- Evidence: Track E enforces this in every stage and Stage 9 validity scan double-checks the counts and banned columns."
    )

    lines.append("## 5. Recommended Priority")
    if "exceeds_threshold" in fairness_df.columns:
        priority_rows = fairness_df.loc[fairness_df["exceeds_threshold"]].copy()
    else:
        priority_rows = pd.DataFrame()
    if priority_rows.empty:
        lines.append(
            "- No metric currently exceeds the configured thresholds "
            f"(demographic_parity_threshold={dp_threshold}, coverage_parity_min_ratio={coverage_threshold})."
        )
    else:
        priority_rows = priority_rows.copy()
        priority_rows["priority_score"] = priority_rows.apply(
            lambda row: _priority_score(row, dp_threshold, coverage_threshold),
            axis=1,
        )
        priority_rows.sort_values("priority_score", ascending=False, inplace=True)
        for _, row in priority_rows.iterrows():
            lines.append(_format_priority_line(row, dp_threshold, coverage_threshold))

    lines.append("\n## Appendix\n- Refer to Track E Stage 8 inputs for additional detail.")
    return "\n".join(lines) + "\n"


def run(config: dict[str, Any]) -> None:
    paths = resolve_paths(config)
    ensure_output_dirs(paths)

    fairness_df = _load_table(paths.tables_dir / "track_e_s7_fairness_metrics.parquet")
    proxy_df = _load_table(paths.tables_dir / "track_e_s6_proxy_correlations.parquet")
    imbalance_df = _load_table(paths.tables_dir / "track_e_s5_imbalance_report.parquet")

    report = build_mitigation_report(fairness_df, proxy_df, imbalance_df, config)

    out_path = paths.tables_dir / "track_e_s8_mitigation_candidates.md"
    out_path.write_text(report, encoding="utf-8")
    logger.info("Wrote mitigation report %s", out_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Stage 8 — Track E Mitigation Candidates")
    parser.add_argument("--config", required=True, help="Path to track_e.yaml config file")
    args = parser.parse_args()
    _config = load_config(args.config)
    run(_config)
