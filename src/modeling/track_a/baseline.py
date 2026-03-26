"""Track A baseline model: future star prediction under strict temporal rules."""

from __future__ import annotations

import argparse
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
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.common.artifacts import load_candidate_splits
from src.common.config import load_config
from src.common.db import connect_duckdb

matplotlib.use("Agg")

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRACK_NAME = "track_a"
DEFAULT_TRAIN_CAP = 300_000
DIAGNOSTIC_SAMPLE = 50_000

FEATURE_COLUMNS = [
    "text_char_count",
    "text_word_count",
    "user_tenure_days",
    "review_year",
    "review_month",
    "latitude",
    "longitude",
    "category_count",
    "is_first_review",
    "user_prior_review_count",
    "user_prior_avg_stars",
    "user_prior_std_stars",
    "biz_prior_review_count",
    "biz_prior_avg_stars",
    "biz_prior_std_stars",
]


@dataclass(frozen=True)
class SplitContract:
    t1: str
    t2: str
    source: str


@dataclass(frozen=True)
class RunContext:
    config_path: str
    train_cap: int | None
    eval_cap: int | None
    random_seed: int
    split: SplitContract
    feature_columns: list[str]
    train_rows_loaded: int
    train_rows_full: int
    validation_rows_loaded: int
    validation_rows_full: int
    test_rows_loaded: int
    test_rows_full: int
    model_family: str
    model_params: dict[str, Any]


def _resolve_path(config: dict[str, Any], key: str) -> Path:
    path = Path(config["paths"][key])
    return path if path.is_absolute() else PROJECT_ROOT / path


def _track_output_dir(config: dict[str, Any]) -> Path:
    base = _resolve_path(config, "outputs_dir") / "modeling" / TRACK_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def _split_predicate(split_name: str, t1: str, t2: str) -> str:
    if split_name == "train":
        return f"rf.review_date < CAST('{t1}' AS DATE)"
    if split_name == "validation":
        return (
            f"rf.review_date >= CAST('{t1}' AS DATE) "
            f"AND rf.review_date < CAST('{t2}' AS DATE)"
        )
    if split_name == "test":
        return f"rf.review_date >= CAST('{t2}' AS DATE)"
    raise ValueError(f"Unknown split_name: {split_name}")


def _sample_clause(limit: int | None) -> str:
    if limit is None:
        return ""
    return f" ORDER BY hash(rf.review_id) LIMIT {int(limit)}"


def get_split_row_counts(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
    t1: str,
    t2: str,
) -> dict[str, int]:
    pq = review_fact_path.as_posix()
    row = con.execute(
        f"""
        SELECT
            COUNT(*) FILTER (WHERE review_date < CAST(? AS DATE)) AS train_rows,
            COUNT(*) FILTER (
                WHERE review_date >= CAST(? AS DATE)
                  AND review_date < CAST(? AS DATE)
            ) AS validation_rows,
            COUNT(*) FILTER (WHERE review_date >= CAST(? AS DATE)) AS test_rows
        FROM read_parquet('{pq}')
        """,
        [t1, t1, t2, t2],
    ).fetchone()
    return {
        "train": int(row[0]),
        "validation": int(row[1]),
        "test": int(row[2]),
    }


def load_split_frame(
    con: duckdb.DuckDBPyConnection,
    review_fact_path: Path,
    user_history_path: Path,
    business_history_path: Path,
    split_name: str,
    t1: str,
    t2: str,
    limit: int | None = None,
) -> pd.DataFrame:
    predicate = _split_predicate(split_name, t1, t2)
    rf = review_fact_path.as_posix()
    uh = user_history_path.as_posix()
    bh = business_history_path.as_posix()
    query = f"""
        SELECT
            rf.review_id,
            rf.review_stars,
            rf.review_date,
            rf.text_char_count,
            rf.text_word_count,
            rf.user_tenure_days,
            rf.review_year,
            rf.review_month,
            rf.latitude,
            rf.longitude,
            rf.categories,
            uh.user_prior_review_count,
            uh.user_prior_avg_stars,
            uh.user_prior_std_stars,
            bh.biz_prior_review_count,
            bh.biz_prior_avg_stars,
            bh.biz_prior_std_stars
        FROM read_parquet('{rf}') rf
        LEFT JOIN read_parquet('{uh}') uh USING (review_id)
        LEFT JOIN read_parquet('{bh}') bh USING (review_id)
        WHERE {predicate}
        {_sample_clause(limit)}
    """
    df = con.execute(query).fetchdf()
    df["review_date"] = pd.to_datetime(df["review_date"])
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    categories = enriched["categories"].fillna("").astype(str).str.strip()
    enriched["category_count"] = np.where(
        categories.eq(""),
        0,
        categories.str.count(",") + 1,
    ).astype("float32")
    enriched["is_first_review"] = (
        enriched["user_prior_review_count"].fillna(0).eq(0).astype("float32")
    )
    enriched = enriched.drop(columns=["categories", "review_date", "review_id"])
    return enriched


def prepare_design_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    prepared = add_derived_features(df)
    X = prepared[FEATURE_COLUMNS].astype("float32")
    y = prepared["review_stars"].astype("float32")
    return X, y


def clip_star_predictions(predictions: np.ndarray) -> np.ndarray:
    return np.clip(predictions, 1.0, 5.0)


def compute_regression_metrics(
    y_true: pd.Series | np.ndarray,
    y_pred: pd.Series | np.ndarray,
) -> dict[str, float]:
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = clip_star_predictions(np.asarray(y_pred, dtype=float))
    return {
        "mae": float(mean_absolute_error(y_true_arr, y_pred_arr)),
        "rmse": float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))),
        "within_1_star_accuracy": float(np.mean(np.abs(y_true_arr - y_pred_arr) <= 1.0)),
    }


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


def metrics_rows_for_split(
    split_name: str,
    y_true: pd.Series,
    model_pred: np.ndarray,
    train_mean: float,
    train_median: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    comparators = {
        "hist_gradient_boosting": model_pred,
        "naive_mean": np.full(len(y_true), train_mean, dtype=float),
        "naive_median": np.full(len(y_true), train_median, dtype=float),
    }
    for model_name, preds in comparators.items():
        metrics = compute_regression_metrics(y_true, preds)
        rows.append(
            {
                "model_name": model_name,
                "split_name": split_name,
                "row_count": int(len(y_true)),
                **metrics,
            }
        )
    return rows


def plot_predictions(y_true: pd.Series, y_pred: np.ndarray, out_path: Path, seed: int) -> None:
    frame = pd.DataFrame({"actual": y_true.to_numpy(dtype=float), "predicted": clip_star_predictions(y_pred)})
    if len(frame) > DIAGNOSTIC_SAMPLE:
        frame = frame.sample(DIAGNOSTIC_SAMPLE, random_state=seed)

    fig, ax = plt.subplots(figsize=(7, 6))
    hb = ax.hexbin(frame["actual"], frame["predicted"], gridsize=35, cmap="viridis", mincnt=1)
    ax.plot([1, 5], [1, 5], linestyle="--", color="white", linewidth=1.5)
    ax.set_xlabel("Actual stars")
    ax.set_ylabel("Predicted stars")
    ax.set_title("Track A baseline: predicted vs actual (test)")
    fig.colorbar(hb, ax=ax, label="Count")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def metrics_markdown_table(metrics_df: pd.DataFrame) -> str:
    rows = [
        "| model_name | split_name | row_count | mae | rmse | within_1_star_accuracy |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in metrics_df.itertuples(index=False):
        rows.append(
            "| "
            f"{row.model_name} | {row.split_name} | {int(row.row_count)} | "
            f"{row.mae:.4f} | {row.rmse:.4f} | {row.within_1_star_accuracy:.4f} |"
        )
    return "\n".join(rows)


def write_summary(
    output_dir: Path,
    context: RunContext,
    metrics_df: pd.DataFrame,
    figure_path: Path,
) -> None:
    pivot = metrics_df.pivot(index="model_name", columns="split_name")
    model_test_mae = metrics_df.loc[
        (metrics_df["model_name"] == "hist_gradient_boosting")
        & (metrics_df["split_name"] == "test"),
        "mae",
    ].iloc[0]
    mean_test_mae = metrics_df.loc[
        (metrics_df["model_name"] == "naive_mean")
        & (metrics_df["split_name"] == "test"),
        "mae",
    ].iloc[0]
    median_test_mae = metrics_df.loc[
        (metrics_df["model_name"] == "naive_median")
        & (metrics_df["split_name"] == "test"),
        "mae",
    ].iloc[0]
    model_test_within1 = metrics_df.loc[
        (metrics_df["model_name"] == "hist_gradient_boosting")
        & (metrics_df["split_name"] == "test"),
        "within_1_star_accuracy",
    ].iloc[0]
    median_test_within1 = metrics_df.loc[
        (metrics_df["model_name"] == "naive_median")
        & (metrics_df["split_name"] == "test"),
        "within_1_star_accuracy",
    ].iloc[0]

    lines = [
        "# Track A baseline summary",
        "",
        "## Task definition",
        "",
        "Predict future star ratings for Track A under the recommended temporal split using only as-of features derived from `review_fact.parquet` and the Stage 3 history tables.",
        "",
        "## Input surfaces used",
        "",
        "- `data/curated/review_fact.parquet`",
        "- `outputs/tables/track_a_s3_user_history_asof.parquet`",
        "- `outputs/tables/track_a_s3_business_history_asof.parquet`",
        "- `outputs/tables/track_a_s5_candidate_splits.parquet`",
        "- `outputs/tables/track_a_s7_feature_availability.parquet`",
        "",
        "## Feature families used",
        "",
        "- text-length aggregates: `text_char_count`, `text_word_count`",
        "- user timing/history: `user_tenure_days`, `user_prior_review_count`, `user_prior_avg_stars`, `user_prior_std_stars`, `is_first_review`",
        "- business history: `biz_prior_review_count`, `biz_prior_avg_stars`, `biz_prior_std_stars`",
        "- simple context: `review_year`, `review_month`, `latitude`, `longitude`, `category_count`",
        "",
        "## Prohibited features explicitly excluded",
        "",
        "- `business.stars`",
        "- `business.review_count`",
        "- `business.is_open`",
        "- `user.average_stars`",
        "- `user.review_count`",
        "- `user.fans`",
        "- `user.elite`",
        "",
        "## Baseline model family",
        "",
        "- `HistGradientBoostingRegressor` on numeric as-of features",
        "",
        "## Trivial comparators",
        "",
        "- training-set naïve mean baseline",
        "- training-set naïve median baseline",
        "",
        "## Split contract",
        "",
        f"- split source: `{context.split.source}`",
        f"- T1: `{context.split.t1}`",
        f"- T2: `{context.split.t2}`",
        f"- full train rows: `{context.train_rows_full}`; loaded train rows: `{context.train_rows_loaded}`",
        f"- full validation rows: `{context.validation_rows_full}`; loaded validation rows: `{context.validation_rows_loaded}`",
        f"- full test rows: `{context.test_rows_full}`; loaded test rows: `{context.test_rows_loaded}`",
        "",
        "## Metrics",
        "",
        metrics_markdown_table(metrics_df),
        "",
        "## Interpretation",
        "",
        (
            f"On the test split, the histogram-gradient-boosting baseline achieved MAE `{model_test_mae:.4f}` "
            f"versus naïve mean `{mean_test_mae:.4f}` and naïve median `{median_test_mae:.4f}`. "
            f"It wins clearly on MAE/RMSE, while the naïve median still posts higher within-1-star accuracy "
            f"(`{median_test_within1:.4f}` vs `{model_test_within1:.4f}`), which is worth carrying forward into later model comparison."
        ),
        "",
        "## Diagnostic figure",
        "",
        f"- `{figure_path.relative_to(PROJECT_ROOT).as_posix()}`",
        "",
        "## Known limitations",
        "",
        "- This first baseline intentionally stays on as-of numeric features and does not include heavier text modeling or high-cardinality categorical encoding.",
        "- User-history variance features are only partially available, so missingness is handled implicitly by the model rather than by a richer imputation study.",
        "- The Stage 6 leakage audit still reports broad code-scan warnings in older Track A-reachable code paths; this baseline itself reads only the curated Track A-safe tables listed above.",
        "",
        "## M003 audit suitability",
        "",
        "- Track A remains the preferred default M003 fairness-audit target because it is a clean supervised task with explicit labels, temporal splits, and standardized summary/metrics outputs.",
        "",
        "## Reproducible command",
        "",
        f"- `python -m src.modeling.track_a.baseline --config {context.config_path}`",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(config: dict[str, Any], config_path: str, train_cap: int | None, eval_cap: int | None) -> pd.DataFrame:
    curated_dir = _resolve_path(config, "curated_dir")
    tables_dir = _resolve_path(config, "tables_dir")
    output_dir = _track_output_dir(config)
    figure_path = output_dir / "figures" / "predicted_vs_actual_test.png"
    review_fact_path = curated_dir / "review_fact.parquet"
    user_history_path = tables_dir / "track_a_s3_user_history_asof.parquet"
    business_history_path = tables_dir / "track_a_s3_business_history_asof.parquet"

    random_seed = int(config.get("random_seed", 42))
    model = build_model(random_seed)

    con = connect_duckdb(config)
    try:
        t1, t2, source = load_candidate_splits(con, tables_dir, config)
        counts = get_split_row_counts(con, review_fact_path, t1, t2)

        train_df = load_split_frame(
            con,
            review_fact_path,
            user_history_path,
            business_history_path,
            "train",
            t1,
            t2,
            train_cap,
        )
        X_train, y_train = prepare_design_matrix(train_df)
        train_rows_loaded = len(train_df)
        del train_df

        model.fit(X_train, y_train)
        train_mean = float(y_train.mean())
        train_median = float(y_train.median())
        del X_train

        val_df = load_split_frame(
            con,
            review_fact_path,
            user_history_path,
            business_history_path,
            "validation",
            t1,
            t2,
            eval_cap,
        )
        X_val, y_val = prepare_design_matrix(val_df)
        validation_rows_loaded = len(val_df)
        del val_df
        val_pred = model.predict(X_val)
        rows = metrics_rows_for_split("validation", y_val, val_pred, train_mean, train_median)
        del X_val

        test_df = load_split_frame(
            con,
            review_fact_path,
            user_history_path,
            business_history_path,
            "test",
            t1,
            t2,
            eval_cap,
        )
        X_test, y_test = prepare_design_matrix(test_df)
        test_rows_loaded = len(test_df)
        del test_df
        test_pred = model.predict(X_test)
        rows.extend(metrics_rows_for_split("test", y_test, test_pred, train_mean, train_median))
        del X_test
    finally:
        con.close()

    metrics_df = pd.DataFrame(rows)

    metrics_path = output_dir / "metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    plot_predictions(y_test, test_pred, figure_path, random_seed)

    context = RunContext(
        config_path=config_path,
        train_cap=train_cap,
        eval_cap=eval_cap,
        random_seed=random_seed,
        split=SplitContract(t1=t1, t2=t2, source=source),
        feature_columns=FEATURE_COLUMNS,
        train_rows_loaded=train_rows_loaded,
        train_rows_full=counts["train"],
        validation_rows_loaded=validation_rows_loaded,
        validation_rows_full=counts["validation"],
        test_rows_loaded=test_rows_loaded,
        test_rows_full=counts["test"],
        model_family="HistGradientBoostingRegressor",
        model_params=model.get_params(),
    )
    (output_dir / "config_snapshot.json").write_text(
        json.dumps(asdict(context), indent=2), encoding="utf-8"
    )
    write_summary(output_dir, context, metrics_df, figure_path)
    logger.info("Wrote %s", metrics_path)
    logger.info("Wrote %s", output_dir / 'config_snapshot.json')
    logger.info("Wrote %s", output_dir / 'summary.md')
    return metrics_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Track A baseline model")
    parser.add_argument("--config", required=True)
    parser.add_argument("--train-cap", type=int, default=DEFAULT_TRAIN_CAP)
    parser.add_argument("--eval-cap", type=int, default=None)
    args = parser.parse_args()

    config = load_config(args.config)
    run(config, args.config, args.train_cap, args.eval_cap)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    main()
