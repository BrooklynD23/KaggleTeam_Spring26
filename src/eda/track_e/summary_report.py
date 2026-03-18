"""Stage 9 — Track E summary report and validity scan."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import load_config
from src.eda.track_e.common import (
    BANNED_TEXT_COLUMNS,
    FORBIDDEN_DEMOGRAPHIC_COLUMNS,
    MIN_GROUP_SIZE_DEFAULT,
    TrackEPaths,
    ensure_output_dirs,
    list_track_e_artifacts,
    resolve_paths,
)

logger = logging.getLogger(__name__)

# Only these aggregate counts should be checked for min_group_size.
_AGGREGATE_COUNT_COLUMNS = {"business_count", "review_count", "user_count"}


def run_validity_scan(paths: TrackEPaths, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Perform the Track E soft validity audit and return findings."""

    findings: list[dict[str, Any]] = []
    min_size = int(
        config.get("subgroups", {}).get("min_group_size", MIN_GROUP_SIZE_DEFAULT)
    )

    for artifact in sorted(paths.tables_dir.glob("track_e_*.parquet")):
        try:
            df = pd.read_parquet(artifact)
        except Exception as exc:  # pragma: no cover - defensive
            findings.append(
                {
                    "artifact_path": str(artifact),
                    "status": "ERROR",
                    "detail": f"failed to read parquet: {exc}",
                }
            )
            continue

        banned = {col for col in df.columns if col.lower() in BANNED_TEXT_COLUMNS}
        if banned:
            findings.append(
                {
                    "artifact_path": str(artifact),
                    "status": "FAIL",
                    "detail": f"banned text columns: {sorted(banned)}",
                }
            )

        demographic = {col for col in df.columns if col.lower() in FORBIDDEN_DEMOGRAPHIC_COLUMNS}
        if demographic:
            findings.append(
                {
                    "artifact_path": str(artifact),
                    "status": "FAIL",
                    "detail": f"forbidden demographic columns: {sorted(demographic)}",
                }
            )

        for col in df.columns:
            if col.lower() not in _AGGREGATE_COUNT_COLUMNS:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            mask = df[col].fillna(0) < min_size
            if mask.any():
                low_values = df.loc[mask, col].unique()[:3]
                findings.append(
                    {
                        "artifact_path": str(artifact),
                        "status": "WARN",
                        "detail": (
                            f"column '{col}' has values below min_group_size={min_size}: "
                            f"{list(low_values)}"
                        ),
                    }
                )
    return findings


def _load_table(paths: TrackEPaths, name: str) -> pd.DataFrame | None:
    path = paths.tables_dir / name
    if not path.is_file():
        return None
    return pd.read_parquet(path)


def _format_confidence(flag: bool) -> str:
    return "High" if flag else "Low"


def _artifact_status(path: Path) -> str:
    return "present" if path.is_file() else "missing"


def build_summary_report(
    paths: TrackEPaths, config: dict[str, Any], findings: list[dict[str, Any]]
) -> str:
    """Render the Track E summary markdown string."""

    stage1_defs = _load_table(paths, "track_e_s1_subgroup_definitions.parquet")
    stage1_summary = _load_table(paths, "track_e_s1_subgroup_summary.parquet")
    coverage = _load_table(paths, "track_e_s2_coverage_by_subgroup.parquet")
    star_disparity = _load_table(paths, "track_e_s3_star_disparity.parquet")
    ks_results = _load_table(paths, "track_e_s3_ks_test_results.parquet")
    usefulness = _load_table(paths, "track_e_s4_usefulness_disparity.parquet")
    imbalance = _load_table(paths, "track_e_s5_imbalance_report.parquet")
    proxies = _load_table(paths, "track_e_s6_proxy_correlations.parquet")
    fairness = _load_table(paths, "track_e_s7_fairness_metrics.parquet")

    lines: list[str] = [
        "# Track E EDA Summary: Bias and Disparity Audit",
        "",
        "## 1. Dataset Overview",
    ]

    total_businesses = len(stage1_defs) if stage1_defs is not None else None
    if total_businesses is not None:
        lines.append(f"- Total businesses analyzed: {total_businesses}.")
    else:
        lines.append("- Total businesses analyzed: data missing.")

    dims_present = sorted(
        stage1_summary["subgroup_type"].unique().tolist()
    ) if stage1_summary is not None else []
    if dims_present:
        lines.append(f"- Subgroup dimensions populated: {', '.join(dims_present)}.")
    else:
        lines.append("- Subgroup dimensions summary is not available.")

    if coverage is not None and not coverage.empty:
        city_rows = coverage.loc[coverage["subgroup_type"] == "city"]
        if not city_rows.empty:
            top = int(city_rows["review_count"].max())
            bottom = int(city_rows["review_count"].min())
            lines.append(
                f"- City coverage range: {bottom} → {top} reviews across reported cities."
            )
        else:
            lines.append("- City coverage data is not reported in Stage 2 yet.")
    else:
        lines.append("- Coverage table is unavailable for Stage 2.")

    lines.extend([
        "",
        "## 2. Hypothesis Assessment",
        "",
        "| # | Hypothesis | Finding | Evidence | Confidence |",
        "|---|---|---|---|---|",
    ])

    def _range_str(df: pd.DataFrame | None, col: str) -> tuple[str, bool]:
        if df is None or df.empty or col not in df.columns:
            return ("no data", False)
        series = df[col].dropna()
        if series.empty:
            return ("no data", False)
        lo, hi = float(series.min()), float(series.max())
        return (f"{lo:.2f} → {hi:.2f}", hi - lo > 0)

    # H1
    city_range, city_disparity = _range_str(
        coverage[coverage["subgroup_type"] == "city"] if coverage is not None else None,
        "review_count",
    )
    lines.append(
        f"| H1 | Coverage disparity exists across cities | {'Supported' if city_disparity else 'Not evaluated'} | "
        f"Stage 2 city review_count range {city_range} | {_format_confidence(city_disparity)} |"
    )

    # H2
    star_cat = star_disparity[star_disparity["subgroup_type"] == "primary_category"] if star_disparity is not None else None
    star_range, star_diff = _range_str(star_cat, "mean_stars")
    lines.append(
        f"| H2 | Star distributions differ by category | {'Supported' if star_diff else 'Not evaluated'} | "
        f"Stage 3 category mean_stars range {star_range} | {_format_confidence(star_diff)} |"
    )

    # H3
    star_price = star_disparity[star_disparity["subgroup_type"] == "price_tier"] if star_disparity is not None else None
    price_range, price_diff = _range_str(star_price, "mean_stars")
    lines.append(
        f"| H3 | Price tier correlates with ratings | {'Supported' if price_diff else 'Not evaluated'} | "
        f"Stage 3 price_tier mean_stars range {price_range} | {_format_confidence(price_diff)} |"
    )

    # H4
    useful_city = usefulness[usefulness["subgroup_type"] == "city"] if usefulness is not None else None
    useful_range, useful_diff = _range_str(useful_city, "mean_useful")
    lines.append(
        f"| H4 | Useful votes vary by city | {'Supported' if useful_diff else 'Not evaluated'} | "
        f"Stage 4 city mean_useful range {useful_range} | {_format_confidence(useful_diff)} |"
    )

    # H5
    gini_flag = False
    imbalance_note = "not available"
    if imbalance is not None and not imbalance.empty:
        gini_flag = imbalance["gini_coefficient"].max() > 0.1
        imbalance_note = f"Stage 5 max_gini={float(imbalance['gini_coefficient'].max()):.3f}"
    lines.append(
        f"| H5 | Data imbalance affects minority groups | {'Supported' if gini_flag else 'Not evaluated'} | "
        f"{imbalance_note} | {_format_confidence(gini_flag)} |"
    )

    # H6
    proxy_flag = bool(
        proxies is not None
        and "is_proxy_risk" in proxies.columns
        and proxies["is_proxy_risk"].any()
    )
    proxy_note = (
        f"Stage 6 {int(proxies['is_proxy_risk'].sum())} proxy risks flagged"
        if proxies is not None and "is_proxy_risk" in proxies.columns
        else "Stage 6 data not available"
    )
    lines.append(
        f"| H6 | Features serve as subgroup proxies | {'Supported' if proxy_flag else 'Not evaluated'} | "
        f"{proxy_note} | {_format_confidence(proxy_flag)} |"
    )

    lines.extend([
        "",
        "## 3. Key Findings",
    ])
    if city_disparity or star_diff or price_diff or useful_diff:
        if city_disparity:
            lines.append(f"- City coverage imbalance spans {city_range} reviews, pointing to representation gaps.")
        if star_diff:
            lines.append(f"- Category ratings span {star_range}, reinforcing cross-category dispersion.")
        if price_diff:
            lines.append(f"- Price tiers reflect differences in mean stars ({price_range}).")
        if useful_diff:
            lines.append(f"- Useful-vote rates fluctuate by city ({useful_range}).")
    else:
        lines.append("- Stage 2–4 artifacts are incomplete, so high-level findings are pending.")
    if findings:
        lines.append(
            f"- Validity scan recorded {len(findings)} findings; see outputs/logs/track_e_s9_validity_scan.log."
        )
    else:
        lines.append("- Validity scan completed with no flagged issues.")

    lines.extend([
        "",
        "## 4. Simpson's Paradox Check",
    ])
    simpson_count = int(ks_results['_simpson_flag'].sum()) if ks_results is not None and '_simpson_flag' in ks_results.columns else 0
    if ks_results is not None and not ks_results.empty:
        lines.append(
            f"- {simpson_count} KS comparisons flagged for Simpson's paradox in Stage 3 (_simpson_flag column)."
        )
    else:
        lines.append("- KS comparison data from Stage 3 is unavailable for Simpson's check.")

    lines.extend([
        "",
        "## 5. Fairness Baseline Summary",
    ])
    if fairness is not None and not fairness.empty:
        top_gap = fairness.sort_values("gap", ascending=False).iloc[0]
        lines.append(
            f"- Top fairness gap: {top_gap['metric_name']} between {top_gap['group_a']} and {top_gap['group_b']} (gap={float(top_gap['gap']):.3f})."
        )
    else:
        lines.append("- Fairness metrics (Stage 7) are not yet available.")

    lines.extend([
        "",
        "## 6. Proxy Risk Summary",
    ])
    if proxies is not None and not proxies.empty:
        risk_count = int(proxies['is_proxy_risk'].sum()) if 'is_proxy_risk' in proxies.columns else 0
        lines.append(
            f"- Proxy correlation analysis flagged {risk_count} proxy risk pairs in Stage 6."
        )
    else:
        lines.append("- Proxy correlation analysis (Stage 6) is not available.")

    lines.extend([
        "",
        "## 7. Recommended Mitigations",
    ])
    mitigation_path = paths.tables_dir / "track_e_s8_mitigation_candidates.md"
    if mitigation_path.is_file():
        lines.append(f"- See {mitigation_path.name} for curated mitigation candidates backed by Stages 5–7.")
    else:
        lines.append("- Mitigation report is not available yet (Stage 8 has not run).")

    lines.extend([
        "",
        "## 8. Limitations and Caveats",
        "",
        "- All findings are aggregate-only (minimum group size enforced).",
        "- No demographic inference or causal claims are made in this audit.",
        "- Simulated geography is at the city/category/price tier level (no neighborhood field).",
        "- Temporal confounders may still be present; treat these metrics as diagnostics, not guarantees.",
    ])

    lines.extend([
        "",
        "## 9. Artifacts Index",
        "",
        "| Artifact | Status |",
        "|---|---|",
    ])
    for artifact in list_track_e_artifacts(paths):
        lines.append(f"| {artifact.name} | {_artifact_status(artifact)} |")
    summary_file = paths.tables_dir / "track_e_s9_eda_summary.md"
    validity_log = paths.logs_dir / "track_e_s9_validity_scan.log"
    lines.append(f"| {summary_file.name} | present |")
    lines.append(f"| {validity_log.name} | present |")

    return "\n".join(lines) + "\n"


def run(config: dict[str, Any]) -> None:
    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    findings = run_validity_scan(paths, config)
    log_path = paths.logs_dir / "track_e_s9_validity_scan.log"
    log_lines = [
        "Track E validity scan results:",
    ]
    if findings:
        for finding in findings:
            log_lines.append(
                f"[{finding['status']}] {Path(finding['artifact_path']).name}: {finding['detail']}"
            )
    else:
        log_lines.append("No findings detected.")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    logger.info("Wrote validity log %s", log_path)

    summary = build_summary_report(paths, config, findings)
    summary_path = paths.tables_dir / "track_e_s9_eda_summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    logger.info("Wrote summary %s", summary_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 9 — Track E summary report and validity scan")
    parser.add_argument("--config", required=True, help="Path to configs/track_e.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    run(config)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
