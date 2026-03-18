"""Stage 7: Feature Availability Matrix for Track A."""

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from src.common.artifacts import load_candidate_splits
from src.common.config import load_config

matplotlib.use("Agg")

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

BASE_FEATURES = (
    "text_char_count",
    "text_word_count",
    "user_tenure_days",
    "city",
    "state",
    "categories",
    "latitude",
    "longitude",
)
USER_HISTORY_FEATURES = (
    "user_prior_review_count",
    "user_prior_avg_stars",
    "user_prior_std_stars",
)
BUSINESS_HISTORY_FEATURES = (
    "biz_prior_review_count",
    "biz_prior_avg_stars",
    "biz_prior_std_stars",
)


def _resolve_path(config: dict[str, Any], key: str) -> Path:
    path = Path(config["paths"][key])
    return path if path.is_absolute() else PROJECT_ROOT / path



def _artifact_path_candidates(tables_dir: Path, stem: str) -> list[Path]:
    return [
        tables_dir / f"{stem}.parquet",
        tables_dir / stem,
    ]


def _existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _add_availability_rows(
    con: duckdb.DuckDBPyConnection,
    rows: list[dict[str, Any]],
    source_query: str,
    features: tuple[str, ...],
    source_artifact: str,
    artifact_status: str,
) -> None:
    if artifact_status == "missing":
        for feature in features:
            for split_name in ("train", "validation", "test"):
                rows.append(
                    {
                        "feature_name": feature,
                        "split_name": split_name,
                        "total_reviews": None,
                        "non_null_reviews": None,
                        "availability_fraction": None,
                        "artifact_status": artifact_status,
                        "source_artifact": source_artifact,
                    }
                )
        return

    for feature in features:
        df = con.execute(
            f"""
            SELECT
                split_name,
                COUNT(*) AS total_reviews,
                COUNT(*) FILTER (WHERE {feature} IS NOT NULL) AS non_null_reviews,
                COUNT(*) FILTER (WHERE {feature} IS NOT NULL) * 1.0 / COUNT(*) AS availability_fraction
            FROM ({source_query})
            GROUP BY split_name
            ORDER BY CASE split_name
                WHEN 'train' THEN 0
                WHEN 'validation' THEN 1
                ELSE 2
            END
            """
        ).fetchdf()
        for row in df.itertuples(index=False):
            rows.append(
                {
                    "feature_name": feature,
                    "split_name": row.split_name,
                    "total_reviews": int(row.total_reviews),
                    "non_null_reviews": int(row.non_null_reviews),
                    "availability_fraction": float(row.availability_fraction),
                    "artifact_status": artifact_status,
                    "source_artifact": source_artifact,
                }
            )


def plot_coverage_bars(df: pd.DataFrame, figures_dir: Path) -> None:
    available = df[df["artifact_status"] == "available"].copy()
    if available.empty:
        logger.warning("No available feature coverage rows to plot.")
        return

    pivot = available.pivot(
        index="feature_name",
        columns="split_name",
        values="availability_fraction",
    ).fillna(0.0)
    pivot = pivot.sort_values(by=["train", "validation", "test"], ascending=False)

    fig, ax = plt.subplots(figsize=(12, 7))
    x = range(len(pivot))
    width = 0.25
    for offset, split_name, color in (
        (-width, "train", "tab:blue"),
        (0.0, "validation", "tab:orange"),
        (width, "test", "tab:green"),
    ):
        if split_name in pivot.columns:
            values = pivot[split_name].tolist()
        else:
            values = [0.0] * len(pivot)
        ax.bar(
            [idx + offset for idx in x],
            values,
            width=width,
            label=split_name,
            color=color,
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")
    ax.set_ylabel("Availability Fraction")
    ax.set_title("Track A Feature Availability by Split")
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()

    out = figures_dir / "track_a_s7_feature_coverage_bars.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def run(config: dict[str, Any]) -> pd.DataFrame:
    curated_dir = _resolve_path(config, "curated_dir")
    tables_dir = _resolve_path(config, "tables_dir")
    figures_dir = _resolve_path(config, "figures_dir")
    review_fact_path = curated_dir / "review_fact.parquet"
    user_history_path = _existing_path(
        _artifact_path_candidates(tables_dir, "track_a_s3_user_history_asof")
    )
    business_history_path = _existing_path(
        _artifact_path_candidates(tables_dir, "track_a_s3_business_history_asof")
    )

    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    try:
        t1, t2, _ = load_candidate_splits(con, tables_dir, config)
        con.execute(
            """
            CREATE OR REPLACE TEMP VIEW review_base AS
            SELECT
                review_id,
                CASE
                    WHEN review_date < CAST(? AS DATE) THEN 'train'
                    WHEN review_date < CAST(? AS DATE) THEN 'validation'
                    ELSE 'test'
                END AS split_name,
                text_char_count,
                text_word_count,
                user_tenure_days,
                city,
                state,
                categories,
                latitude,
                longitude
            FROM read_parquet(?)
            """,
            [t1, t2, str(review_fact_path)],
        )

        rows: list[dict[str, Any]] = []
        _add_availability_rows(
            con,
            rows,
            "SELECT * FROM review_base",
            BASE_FEATURES,
            "data/curated/review_fact.parquet",
            "available",
        )

        if user_history_path is not None:
            user_query = f"""
                SELECT
                    rb.split_name,
                    uh.user_prior_review_count,
                    uh.user_prior_avg_stars,
                    uh.user_prior_std_stars
                FROM review_base rb
                LEFT JOIN read_parquet('{user_history_path.as_posix()}') uh
                    USING (review_id)
            """
            _add_availability_rows(
                con,
                rows,
                user_query,
                USER_HISTORY_FEATURES,
                user_history_path.name,
                "available",
            )
        else:
            _add_availability_rows(
                con,
                rows,
                "",
                USER_HISTORY_FEATURES,
                "track_a_s3_user_history_asof.parquet",
                "missing",
            )

        if business_history_path is not None:
            business_query = f"""
                SELECT
                    rb.split_name,
                    bh.biz_prior_review_count,
                    bh.biz_prior_avg_stars,
                    bh.biz_prior_std_stars
                FROM review_base rb
                LEFT JOIN read_parquet('{business_history_path.as_posix()}') bh
                    USING (review_id)
            """
            _add_availability_rows(
                con,
                rows,
                business_query,
                BUSINESS_HISTORY_FEATURES,
                business_history_path.name,
                "available",
            )
        else:
            _add_availability_rows(
                con,
                rows,
                "",
                BUSINESS_HISTORY_FEATURES,
                "track_a_s3_business_history_asof.parquet",
                "missing",
            )
    finally:
        con.close()

    df = pd.DataFrame(rows)
    out = tables_dir / "track_a_s7_feature_availability.parquet"
    df.to_parquet(out, index=False)
    logger.info("Wrote %s (%d rows)", out, len(df))
    plot_coverage_bars(df, figures_dir)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage 7: Feature Availability Matrix",
    )
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
