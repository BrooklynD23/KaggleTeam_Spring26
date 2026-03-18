"""Stage 8: Consolidated markdown summary for Track A EDA."""

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb

from src.common.artifacts import load_candidate_splits
from src.common.config import load_config

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_path(config: dict[str, Any], key: str) -> Path:
    path = Path(config["paths"][key])
    return path if path.is_absolute() else PROJECT_ROOT / path


def _figure_link(figures_dir: Path, name: str) -> str:
    figure_path = figures_dir / name
    if not figure_path.is_file():
        return ""
    return f"- `{figure_path.relative_to(figures_dir.parent).as_posix()}`"


def _artifact_status(path: Path) -> str:
    return "present" if path.is_file() else "missing"


def _load_one_row(con: duckdb.DuckDBPyConnection, path: Path, query: str) -> tuple[Any, ...] | None:
    if not path.is_file():
        return None
    return con.execute(query, [str(path)]).fetchone()


def _build_markdown(config: dict[str, Any]) -> str:
    tables_dir = _resolve_path(config, "tables_dir")
    figures_dir = _resolve_path(config, "figures_dir")
    table_paths = {
        "stage_1_periods": tables_dir / "track_a_s1_review_volume_by_period.parquet",
        "stage_2_text": tables_dir / "track_a_s2_text_length_stats.parquet",
        "stage_3_history": tables_dir / "track_a_s3_user_history_depth.parquet",
        "stage_5_splits": tables_dir / "track_a_s5_candidate_splits.parquet",
        "stage_6_leakage": tables_dir / "track_a_s6_leakage_report.parquet",
        "stage_7_availability": tables_dir / "track_a_s7_feature_availability.parquet",
    }

    con = duckdb.connect()
    try:
        stage1 = _load_one_row(
            con,
            table_paths["stage_1_periods"],
            """
            SELECT
                COUNT(*) AS n_periods,
                MIN(period)::VARCHAR AS first_period,
                MAX(period)::VARCHAR AS last_period,
                SUM(review_count) AS total_reviews
            FROM read_parquet(?)
            """,
        )
        stage2 = _load_one_row(
            con,
            table_paths["stage_2_text"],
            """
            SELECT
                ROUND(AVG(mean_words), 2) AS avg_mean_words,
                MAX(max_words) AS max_words
            FROM read_parquet(?)
            """,
        )
        stage3 = _load_one_row(
            con,
            table_paths["stage_3_history"],
            """
            SELECT
                SUM(n_reviews) AS total_reviews,
                SUM(CASE WHEN bucket = '0 (first review)' THEN n_reviews ELSE 0 END) AS first_review_count
            FROM read_parquet(?)
            """,
        )
        stage5_t1, stage5_t2, _ = load_candidate_splits(con, tables_dir, config)
        stage5 = (stage5_t1, stage5_t2) if stage5_t1 else None
        stage6 = _load_one_row(
            con,
            table_paths["stage_6_leakage"],
            """
            SELECT
                SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS fail_checks,
                SUM(CASE WHEN status = 'WARN' THEN 1 ELSE 0 END) AS warn_checks
            FROM read_parquet(?)
            """,
        )
        stage7 = _load_one_row(
            con,
            table_paths["stage_7_availability"],
            """
            SELECT
                feature_name,
                split_name,
                availability_fraction
            FROM read_parquet(?)
            WHERE artifact_status = 'available'
            ORDER BY availability_fraction ASC, feature_name ASC
            LIMIT 1
            """,
        )
    finally:
        con.close()

    lines = [
        "# Track A EDA Summary",
        "",
        "## Artifact Status",
        "",
        "| Artifact | Status |",
        "|---|---|",
    ]
    for label, path in table_paths.items():
        lines.append(f"| {label} | {_artifact_status(path)} |")

    lines.extend(
        [
            "",
            "## Key Findings",
            "",
        ]
    )

    if stage1 is not None:
        lines.append(
            f"- Stage 1 covers {int(stage1[0])} periods from {stage1[1]} to {stage1[2]} across {int(stage1[3])} reviews."
        )
    else:
        lines.append("- Stage 1 artifacts are missing, so temporal profile findings are unavailable.")

    if stage2 is not None:
        lines.append(
            f"- Stage 2 text-length outputs report an average mean word count of {stage2[0]} and a maximum observed word count of {int(stage2[1])}."
        )
    else:
        lines.append("- Stage 2 artifacts are missing, so text-profile findings are unavailable.")

    if stage3 is not None and stage3[0]:
        first_review_share = float(stage3[1]) / float(stage3[0]) if stage3[1] is not None else 0.0
        lines.append(
            f"- Stage 3 history profiling marks {int(stage3[1] or 0)} of {int(stage3[0])} reviews as first-review rows ({first_review_share:.1%})."
        )
    else:
        lines.append("- Stage 3 artifacts are missing, so user-history findings are unavailable.")

    if stage5 is not None:
        lines.append(f"- Stage 5 selected split candidates start at T1={stage5[0]} and T2={stage5[1]}.")
    else:
        splits = config.get("splits", {})
        lines.append(
            f"- Stage 5 artifacts are missing; config defaults remain T1={splits.get('t1')} and T2={splits.get('t2')}."
        )

    if stage6 is not None:
        lines.append(
            f"- Stage 6 leakage audit currently reports {int(stage6[0] or 0)} failing checks and {int(stage6[1] or 0)} warnings."
        )
    else:
        lines.append("- Stage 6 leakage audit artifact is missing.")

    if stage7 is not None:
        lines.append(
            f"- Stage 7 shows the weakest available feature coverage for `{stage7[0]}` in `{stage7[1]}` at {float(stage7[2]):.1%}."
        )
    else:
        lines.append("- Stage 7 feature availability artifact is missing or has no available-feature rows.")

    lines.extend(
        [
            "",
            "## Figure References",
            "",
        ]
    )
    figure_lines = [
        _figure_link(figures_dir, "track_a_s1_star_distribution_over_time.png"),
        _figure_link(figures_dir, "track_a_s1_review_volume_timeline.png"),
        _figure_link(figures_dir, "track_a_s2_text_length_by_star.png"),
        _figure_link(figures_dir, "track_a_s2_text_length_distribution.png"),
        _figure_link(figures_dir, "track_a_s3_user_prior_review_count_dist.png"),
        _figure_link(figures_dir, "track_a_s3_user_tenure_vs_rating_var.png"),
        _figure_link(figures_dir, "track_a_s4_attr_null_rate_heatmap.png"),
        _figure_link(figures_dir, "track_a_s5_split_comparison.png"),
        _figure_link(figures_dir, "track_a_s7_feature_coverage_bars.png"),
    ]
    figure_lines = [line for line in figure_lines if line]
    if figure_lines:
        lines.extend(figure_lines)
    else:
        lines.append("- No figure artifacts were found.")

    lines.extend(
        [
            "",
            "## Next Checks",
            "",
            "- Confirm Stage 5 has written the recommended split artifact before using Stage 6 overlap counts for sign-off.",
            "- Review `outputs/logs/track_a_s6_leakage_audit.log` if any failing leakage checks are present.",
            "- Re-run this summary after Stage 4 and Stage 5 outputs exist to replace fallback notes with measured results.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(config: dict[str, Any]) -> Path:
    tables_dir = _resolve_path(config, "tables_dir")
    tables_dir.mkdir(parents=True, exist_ok=True)
    out = tables_dir / "track_a_s8_eda_summary.md"
    out.write_text(_build_markdown(config), encoding="utf-8")
    logger.info("Wrote %s", out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 8: Track A summary report")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    run(config)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
