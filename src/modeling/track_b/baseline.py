"""Track B baseline model: snapshot usefulness ranking within age-controlled groups."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_squared_error

from src.common.config import load_config
from src.common.db import connect_duckdb
from src.eda.track_b.common import create_snapshot_view, resolve_paths

matplotlib.use("Agg")

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRACK_NAME = "track_b"
DEFAULT_TRAIN_CAP = 400_000
FEATURE_COLUMNS = [
    "text_char_count",
    "text_word_count",
    "review_stars",
    "fans",
    "user_tenure_days",
    "is_open",
    "elite_flag",
    "review_year",
    "review_month",
    "latitude",
    "longitude",
]


@dataclass(frozen=True)
class SplitCounts:
    train_groups: int
    validation_groups: int
    test_groups: int
    train_rows_loaded: int
    train_rows_full: int
    validation_rows_loaded: int
    validation_rows_full: int
    test_rows_loaded: int
    test_rows_full: int


@dataclass(frozen=True)
class RunContext:
    config_path: str
    random_seed: int
    train_cap: int | None
    target_label: str
    feature_columns: list[str]
    snapshot_reference_date: str
    dataset_release_tag: str
    split_counts: SplitCounts
    model_family: str
    model_params: dict[str, Any]


def _track_output_dir(config: dict[str, Any]) -> Path:
    base = Path(config["paths"]["outputs_dir"]) / "modeling" / TRACK_NAME
    if not base.is_absolute():
        base = PROJECT_ROOT / base
    base.mkdir(parents=True, exist_ok=True)
    return base


def stable_group_bucket(group_key: str) -> int:
    digest = hashlib.md5(group_key.encode("utf-8"), usedforsecurity=False).hexdigest()
    return int(digest[:8], 16) % 10


def split_name_for_group(group_key: str) -> str:
    bucket = stable_group_bucket(group_key)
    if bucket <= 6:
        return "train"
    if bucket == 7:
        return "validation"
    return "test"


def ndcg_at_k(relevances: np.ndarray, scores: np.ndarray, k: int = 10) -> float:
    if len(relevances) == 0:
        return 0.0
    order = np.argsort(-scores, kind="mergesort")[:k]
    ideal = np.argsort(-relevances, kind="mergesort")[:k]
    ranked_rels = np.asarray(relevances, dtype=float)[order]
    ideal_rels = np.asarray(relevances, dtype=float)[ideal]
    discounts = 1.0 / np.log2(np.arange(2, len(ranked_rels) + 2))
    dcg = float(np.sum(ranked_rels * discounts))
    ideal_discounts = 1.0 / np.log2(np.arange(2, len(ideal_rels) + 2))
    idcg = float(np.sum(ideal_rels * ideal_discounts))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(binary_labels: np.ndarray, scores: np.ndarray, k: int = 10) -> float | None:
    positives = int(np.sum(binary_labels))
    if positives == 0:
        return None
    order = np.argsort(-scores, kind="mergesort")[:k]
    hits = int(np.sum(np.asarray(binary_labels)[order]))
    return hits / positives


def _load_label_candidates(con: duckdb.DuckDBPyConnection, label_path: Path) -> None:
    pq = label_path.as_posix()
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW track_b_label_candidates_model AS
        SELECT * FROM read_parquet('{pq}')
        """
    )


def load_modeling_frame(
    con: duckdb.DuckDBPyConnection,
    config: dict[str, Any],
    train_cap: int | None,
) -> tuple[pd.DataFrame, dict[str, str], dict[str, int], dict[str, int]]:
    paths = resolve_paths(config)
    metadata = create_snapshot_view(con, config, paths)
    label_path = paths.tables_dir / "track_b_s4_label_candidates.parquet"
    if not label_path.is_file():
        raise FileNotFoundError(f"Missing Track B label candidates: {label_path}")
    _load_label_candidates(con, label_path)

    frame = con.execute(
        """
        SELECT
            labels.review_id,
            labels.group_type,
            labels.group_id,
            labels.age_bucket,
            labels.useful,
            labels.top_decile_label,
            labels.within_group_percentile,
            snapshot.text_char_count,
            snapshot.text_word_count,
            snapshot.review_stars,
            snapshot.fans,
            snapshot.user_tenure_days,
            snapshot.is_open,
            snapshot.elite_flag,
            snapshot.review_year,
            snapshot.review_month,
            snapshot.latitude,
            snapshot.longitude
        FROM track_b_label_candidates_model AS labels
        JOIN review_usefulness_snapshot AS snapshot USING (review_id)
        ORDER BY labels.group_type, labels.group_id, labels.age_bucket, labels.review_id
        """
    ).fetchdf()

    frame["group_key"] = (
        frame["group_type"].astype(str)
        + "|"
        + frame["group_id"].astype(str)
        + "|"
        + frame["age_bucket"].astype(str)
    )
    frame["split_name"] = frame["group_key"].map(split_name_for_group)

    full_group_counts = frame.groupby("split_name")["group_key"].nunique().astype(int).to_dict()
    full_row_counts = frame.groupby("split_name").size().astype(int).to_dict()

    if train_cap is not None:
        train_mask = frame["split_name"] == "train"
        train_df = frame.loc[train_mask].copy()
        if len(train_df) > train_cap:
            train_df = train_df.sample(train_cap, random_state=int(config.get("random_seed", 42)))
        frame = pd.concat([train_df, frame.loc[~train_mask]], ignore_index=True)

    return frame, metadata, full_group_counts, full_row_counts


def prepare_design_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = frame[FEATURE_COLUMNS].astype("float32")
    y = frame["within_group_percentile"].astype("float32")
    return X, y


def build_model(random_seed: int) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_iter=200,
        max_depth=6,
        min_samples_leaf=50,
        l2_regularization=1.0,
        random_state=random_seed,
    )


def evaluate_ranking(frame: pd.DataFrame, score_column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (split_name, age_bucket), bucket_df in frame.groupby(["split_name", "age_bucket"], sort=False):
        ndcgs: list[float] = []
        recalls: list[float] = []
        represented_groups = 0
        for _, group_df in bucket_df.groupby("group_key", sort=False):
            if len(group_df) < 2:
                continue
            represented_groups += 1
            ndcgs.append(
                ndcg_at_k(
                    group_df["useful"].to_numpy(dtype=float),
                    group_df[score_column].to_numpy(dtype=float),
                    k=10,
                )
            )
            recall = recall_at_k(
                group_df["top_decile_label"].to_numpy(dtype=int),
                group_df[score_column].to_numpy(dtype=float),
                k=10,
            )
            if recall is not None:
                recalls.append(recall)
        rows.append(
            {
                "model_name": score_column,
                "split_name": split_name,
                "age_bucket": age_bucket,
                "represented_groups": represented_groups,
                "ndcg_at_10": float(np.mean(ndcgs)) if ndcgs else 0.0,
                "recall_at_10_top_decile": float(np.mean(recalls)) if recalls else np.nan,
            }
        )

    result = pd.DataFrame(rows)
    overall = (
        result.groupby(["model_name", "split_name"], as_index=False)
        .agg(
            represented_groups=("represented_groups", "sum"),
            ndcg_at_10=("ndcg_at_10", "mean"),
            recall_at_10_top_decile=("recall_at_10_top_decile", "mean"),
        )
        .assign(age_bucket="ALL")
    )
    return pd.concat([result, overall], ignore_index=True)


def plot_test_ndcg(metrics_df: pd.DataFrame, out_path: Path) -> None:
    plot_df = metrics_df[
        (metrics_df["split_name"] == "test") & (metrics_df["age_bucket"] != "ALL")
    ].copy()
    if plot_df.empty:
        return
    pivot = plot_df.pivot(index="age_bucket", columns="model_name", values="ndcg_at_10")
    fig, ax = plt.subplots(figsize=(11, 7))
    pivot.plot(kind="bar", ax=ax)
    ax.set_xlabel("Age bucket")
    ax.set_ylabel("NDCG@10")
    ax.set_title("Track B baseline: test NDCG@10 by age bucket")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def metrics_markdown_table(metrics_df: pd.DataFrame) -> str:
    rows = [
        "| model_name | split_name | age_bucket | represented_groups | ndcg_at_10 | recall_at_10_top_decile |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in metrics_df.itertuples(index=False):
        recall = "nan" if pd.isna(row.recall_at_10_top_decile) else f"{row.recall_at_10_top_decile:.4f}"
        rows.append(
            f"| {row.model_name} | {row.split_name} | {row.age_bucket} | {int(row.represented_groups)} | {row.ndcg_at_10:.4f} | {recall} |"
        )
    return "\n".join(rows)


def write_summary(
    output_dir: Path,
    context: RunContext,
    ranking_metrics: pd.DataFrame,
    figure_path: Path,
) -> None:
    test_overall = ranking_metrics[
        (ranking_metrics["split_name"] == "test") & (ranking_metrics["age_bucket"] == "ALL")
    ].set_index("model_name")
    model_ndcg = float(test_overall.loc["pointwise_percentile_regressor", "ndcg_at_10"])
    length_ndcg = float(test_overall.loc["text_length_only", "ndcg_at_10"])
    stars_ndcg = float(test_overall.loc["review_stars_only", "ndcg_at_10"])
    model_recall = float(test_overall.loc["pointwise_percentile_regressor", "recall_at_10_top_decile"])

    lines = [
        "# Track B baseline summary",
        "",
        "## Task definition",
        "",
        "Rank comparatively useful reviews within age-controlled snapshot groups using a pointwise baseline that respects Track B's snapshot-only framing.",
        "",
        "## Input surfaces used",
        "",
        "- `data/curated/review_fact_track_b.parquet`",
        "- `data/curated/snapshot_metadata.json`",
        "- `outputs/tables/track_b_s4_label_candidates.parquet`",
        "- `outputs/tables/track_b_s6_pairwise_stats.parquet`",
        "- `outputs/tables/track_b_s6_listwise_stats.parquet`",
        "",
        "## Feature families used",
        "",
        "- text-length aggregates: `text_char_count`, `text_word_count`",
        "- review metadata: `review_stars`, `review_year`, `review_month`",
        "- user/account context: `fans`, `user_tenure_days`, `elite_flag`",
        "- business/location context: `is_open`, `latitude`, `longitude`",
        "",
        "## Prohibited features explicitly excluded",
        "",
        "- `review.funny`",
        "- `review.cool`",
        "- any vote-growth or future-usefulness target reconstruction",
        "",
        "## Baseline model family",
        "",
        "- `HistGradientBoostingRegressor` trained pointwise on Stage 4 `within_group_percentile` labels",
        "",
        "## Trivial comparators",
        "",
        "- `text_length_only` score using `text_word_count`",
        "- `review_stars_only` score using `review_stars`",
        "",
        "## Snapshot contract",
        "",
        f"- snapshot reference date: `{context.snapshot_reference_date}`",
        f"- dataset release tag: `{context.dataset_release_tag}`",
        "- group split strategy: deterministic hash split on `group_type|group_id|age_bucket` so whole ranking groups stay together",
        f"- train groups: `{context.split_counts.train_groups}`; validation groups: `{context.split_counts.validation_groups}`; test groups: `{context.split_counts.test_groups}`",
        f"- loaded train rows: `{context.split_counts.train_rows_loaded}` of `{context.split_counts.train_rows_full}` full train rows",
        f"- validation rows: `{context.split_counts.validation_rows_loaded}` of `{context.split_counts.validation_rows_full}`",
        f"- test rows: `{context.split_counts.test_rows_loaded}` of `{context.split_counts.test_rows_full}`",
        "",
        "## Metrics",
        "",
        metrics_markdown_table(ranking_metrics),
        "",
        "## Interpretation",
        "",
        (
            f"On held-out test groups, the pointwise percentile regressor reached overall NDCG@10 `{model_ndcg:.4f}` "
            f"versus `text_length_only` `{length_ndcg:.4f}` and `review_stars_only` `{stars_ndcg:.4f}`. "
            f"Its overall Recall@10 on Stage 4 top-decile labels was `{model_recall:.4f}`."
        ),
        "",
        "## Diagnostic figure",
        "",
        f"- `{figure_path.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Known limitations",
        "",
        "- This baseline stays pointwise on the Stage 4 primary label and does not attempt pairwise or listwise learning in M002.",
        "- Because ranking is evaluated within age-controlled groups, an age-only comparator would be degenerate; the reported trivial comparators stay snapshot-safe while remaining rankable inside groups.",
        "- The model uses only simple numeric snapshot-safe features and does not attempt richer category encoding or cross-group calibration.",
        "",
        "## M003 / later-modeling relevance",
        "",
        "- Track B is now a real ranking lane with reproducible NDCG@10 evidence, but it is not the default M003 fairness-audit target because Track A remains the cleaner supervised baseline for that role.",
        "",
        "## Reproducible command",
        "",
        f"- `python -m src.modeling.track_b.baseline --config {context.config_path}`",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(config: dict[str, Any], config_path: str, train_cap: int | None) -> pd.DataFrame:
    output_dir = _track_output_dir(config)
    figure_path = output_dir / "figures" / "test_ndcg_by_age_bucket.png"
    random_seed = int(config.get("random_seed", 42))
    model = build_model(random_seed)

    con = connect_duckdb(config)
    try:
        frame, metadata, full_group_counts, full_row_counts = load_modeling_frame(con, config, train_cap)
    finally:
        con.close()

    loaded_group_counts = frame.groupby("split_name")["group_key"].nunique().astype(int).to_dict()
    loaded_row_counts = frame.groupby("split_name").size().astype(int).to_dict()

    train_frame = frame.loc[frame["split_name"] == "train"].copy()
    val_frame = frame.loc[frame["split_name"] == "validation"].copy()
    test_frame = frame.loc[frame["split_name"] == "test"].copy()

    X_train, y_train = prepare_design_matrix(train_frame)
    model.fit(X_train, y_train)

    val_frame["pointwise_percentile_regressor"] = model.predict(val_frame[FEATURE_COLUMNS].astype("float32"))
    test_frame["pointwise_percentile_regressor"] = model.predict(test_frame[FEATURE_COLUMNS].astype("float32"))
    for eval_frame in (val_frame, test_frame):
        eval_frame["text_length_only"] = eval_frame["text_word_count"].astype(float)
        eval_frame["review_stars_only"] = eval_frame["review_stars"].astype(float)

    ranking_metrics = pd.concat(
        [
            evaluate_ranking(val_frame, "pointwise_percentile_regressor"),
            evaluate_ranking(val_frame, "text_length_only"),
            evaluate_ranking(val_frame, "review_stars_only"),
            evaluate_ranking(test_frame, "pointwise_percentile_regressor"),
            evaluate_ranking(test_frame, "text_length_only"),
            evaluate_ranking(test_frame, "review_stars_only"),
        ],
        ignore_index=True,
    )
    ranking_metrics = ranking_metrics.sort_values(["split_name", "age_bucket", "model_name"]).reset_index(drop=True)
    ranking_metrics.to_csv(output_dir / "metrics.csv", index=False)

    plot_test_ndcg(ranking_metrics, figure_path)

    context = RunContext(
        config_path=config_path,
        random_seed=random_seed,
        train_cap=train_cap,
        target_label="within_group_percentile",
        feature_columns=FEATURE_COLUMNS,
        snapshot_reference_date=metadata["snapshot_reference_date"],
        dataset_release_tag=metadata["dataset_release_tag"],
        split_counts=SplitCounts(
            train_groups=int(loaded_group_counts.get("train", 0)),
            validation_groups=int(full_group_counts.get("validation", 0)),
            test_groups=int(full_group_counts.get("test", 0)),
            train_rows_loaded=int(loaded_row_counts.get("train", 0)),
            train_rows_full=int(full_row_counts.get("train", 0)),
            validation_rows_loaded=int(loaded_row_counts.get("validation", 0)),
            validation_rows_full=int(full_row_counts.get("validation", 0)),
            test_rows_loaded=int(loaded_row_counts.get("test", 0)),
            test_rows_full=int(full_row_counts.get("test", 0)),
        ),
        model_family="HistGradientBoostingRegressor",
        model_params=model.get_params(),
    )
    (output_dir / "config_snapshot.json").write_text(json.dumps(asdict(context), indent=2), encoding="utf-8")
    write_summary(output_dir, context, ranking_metrics, figure_path)
    logger.info("Wrote %s", output_dir / "metrics.csv")
    logger.info("Wrote %s", output_dir / "config_snapshot.json")
    logger.info("Wrote %s", output_dir / "summary.md")
    return ranking_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Track B baseline model")
    parser.add_argument("--config", required=True)
    parser.add_argument("--train-cap", type=int, default=DEFAULT_TRAIN_CAP)
    args = parser.parse_args()

    config = load_config(args.config)
    run(config, args.config, args.train_cap)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
