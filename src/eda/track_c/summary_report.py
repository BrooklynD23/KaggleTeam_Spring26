"""Stage 9: Summary report for Track C."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from src.common.config import load_config
from src.eda.track_c.common import (
    ensure_output_dirs,
    resolve_paths,
    scan_track_c_text_leaks,
)

logger = logging.getLogger(__name__)


def _read_if_present(path: Path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    return pd.read_parquet(path)


def _artifact_status(path: Path) -> str:
    return "present" if path.is_file() else "missing"


def build_summary(paths) -> str:
    """Render the Track C summary markdown."""
    stage1 = _read_if_present(paths.tables_dir / "track_c_s1_city_coverage.parquet")
    stage2 = _read_if_present(paths.tables_dir / "track_c_s2_review_volume_by_month.parquet")
    stage4 = _read_if_present(paths.tables_dir / "track_c_s4_sentiment_by_city_month.parquet")
    stage5 = _read_if_present(paths.tables_dir / "track_c_s5_keyword_trends.parquet")
    stage6 = _read_if_present(paths.tables_dir / "track_c_s6_sentiment_drift_by_city.parquet")
    stage7 = _read_if_present(paths.tables_dir / "track_c_s7_event_candidates.parquet")
    stage8 = _read_if_present(paths.tables_dir / "track_c_s8_checkin_sentiment_correlation.parquet")
    text_leaks = scan_track_c_text_leaks(paths)

    lines = [
        "# Track C EDA Summary",
        "",
        "## Artifact Status",
        "",
        "| Artifact | Status |",
        "|---|---|",
    ]
    for artifact in sorted(paths.tables_dir.glob("track_c_*")):
        lines.append(f"| {artifact.name} | {_artifact_status(artifact)} |")

    lines.extend(["", "## Key Findings", ""])
    if stage1 is not None and not stage1.empty:
        analyzable = int(stage1["is_analyzable"].fillna(False).sum())
        lines.append(f"- Analyzable cities: {analyzable}.")
    else:
        lines.append("- Stage 1 city coverage artifact is missing.")

    if stage2 is not None and not stage2.empty:
        lines.append(
            f"- Temporal coverage spans {stage2['year_month'].min()} to {stage2['year_month'].max()}."
        )
    else:
        lines.append("- Stage 2 temporal binning artifact is missing.")

    if stage4 is not None and not stage4.empty:
        corr = spearmanr(stage4["mean_stars"], stage4["mean_sentiment"]).statistic
        lines.append(
            f"- Aggregate sentiment/star Spearman correlation: {float(corr):.4f}."
        )
    else:
        lines.append("- Stage 4 sentiment artifact is missing.")

    if stage5 is not None and not stage5.empty:
        top_keyword = (
            stage5.groupby("keyword")["frequency"].sum().sort_values(ascending=False).index[0]
        )
        lines.append(f"- Most common tracked keyword: `{top_keyword}`.")
    else:
        lines.append("- Stage 5 keyword trend artifact is missing.")

    if stage6 is not None and not stage6.empty:
        significant = int(stage6["is_significant"].fillna(False).sum())
        lines.append(f"- Significant sentiment drift rows: {significant}.")
    else:
        lines.append("- Stage 6 drift artifact is missing.")

    if stage7 is not None and not stage7.empty:
        top_city = stage7.sort_values("closure_candidate_count", ascending=False).iloc[0]["city"]
        lines.append(f"- Highest closure-candidate city: `{top_city}`.")
    else:
        lines.append("- Stage 7 event candidate artifact is missing.")

    if stage8 is not None and not stage8.empty:
        best_city = stage8.sort_values("paired_months", ascending=False).iloc[0]["city"]
        lines.append(f"- Best-covered check-in correlation city: `{best_city}`.")
    else:
        lines.append("- Stage 8 check-in correlation artifact is missing.")

    lines.extend(["", "## Text Leak Scan", ""])
    if not text_leaks:
        lines.append("- No Track C parquet artifacts were available to scan.")
    else:
        for finding in text_leaks:
            lines.append(
                f"- [{finding['status']}] `{Path(finding['artifact_path']).name}`: {finding['detail']}"
            )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Geography is city/state only; neighborhood analysis is deferred.",
            "- The text leak scan is soft and does not block summary generation.",
            "- Event candidates are descriptive proxies, not causal claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 9: Summary Report")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    paths = resolve_paths(config)
    ensure_output_dirs(paths)
    out = paths.tables_dir / "track_c_s9_eda_summary.md"
    out.write_text(build_summary(paths), encoding="utf-8")
    logger.info("Wrote %s", out)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
