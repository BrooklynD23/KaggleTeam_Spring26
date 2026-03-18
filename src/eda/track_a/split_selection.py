"""Stage 5: Candidate temporal split analysis for Track A."""

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import ks_2samp

from src.common.config import load_config

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _resolve(config: dict[str, Any], key: str) -> Path:
    return Path(config["paths"][key])


def load_reviews(con: duckdb.DuckDBPyConnection, review_fact_path: Path) -> pd.DataFrame:
    """Load review dates and stars from the Track A curated table."""
    df = con.execute(
        """
        SELECT review_id, review_date, review_stars
        FROM read_parquet($1)
        WHERE review_date IS NOT NULL
        ORDER BY review_date, review_id
        """,
        [str(review_fact_path)],
    ).fetchdf()
    df["review_date"] = pd.to_datetime(df["review_date"])
    return df


def _date_at_percentile(unique_dates: pd.Series, percentile: int) -> pd.Timestamp:
    index = int(round((len(unique_dates) - 1) * (percentile / 100.0)))
    index = min(max(index, 0), len(unique_dates) - 1)
    return pd.Timestamp(unique_dates.iloc[index])


def evaluate_candidates(
    reviews: pd.DataFrame,
    candidate_cfg: list[dict[str, int]],
    min_split_fraction: float,
    ks_threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate configured candidate split pairs."""
    if reviews.empty or not candidate_cfg:
        return pd.DataFrame(), pd.DataFrame()

    unique_dates = pd.Series(reviews["review_date"].sort_values().drop_duplicates().to_list())
    candidate_rows: list[dict[str, Any]] = []
    balance_rows: list[dict[str, Any]] = []

    for idx, candidate in enumerate(candidate_cfg, start=1):
        t1 = _date_at_percentile(unique_dates, int(candidate["t1_pct"]))
        t2 = _date_at_percentile(unique_dates, int(candidate["t2_pct"]))
        if t2 <= t1:
            next_index = unique_dates.searchsorted(t1) + 1
            next_index = min(next_index, len(unique_dates) - 1)
            t2 = pd.Timestamp(unique_dates.iloc[next_index])

        split_df = reviews.copy()
        split_df["split_name"] = "val"
        split_df.loc[split_df["review_date"] < t1, "split_name"] = "train"
        split_df.loc[split_df["review_date"] >= t2, "split_name"] = "test"

        counts = split_df["split_name"].value_counts()
        total_rows = len(split_df)
        train_rows = int(counts.get("train", 0))
        val_rows = int(counts.get("val", 0))
        test_rows = int(counts.get("test", 0))
        min_fraction = min(train_rows, val_rows, test_rows) / total_rows if total_rows else 0.0

        train_stars = split_df.loc[split_df["split_name"] == "train", "review_stars"]
        val_stars = split_df.loc[split_df["split_name"] == "val", "review_stars"]
        test_stars = split_df.loc[split_df["split_name"] == "test", "review_stars"]

        ks_train_val = ks_2samp(train_stars, val_stars).statistic if len(train_stars) and len(val_stars) else None
        ks_train_test = ks_2samp(train_stars, test_stars).statistic if len(train_stars) and len(test_stars) else None
        ks_val_test = ks_2samp(val_stars, test_stars).statistic if len(val_stars) and len(test_stars) else None

        candidate_id = f"candidate_{idx}"
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "t1_pct": int(candidate["t1_pct"]),
                "t2_pct": int(candidate["t2_pct"]),
                "t1": t1.date().isoformat(),
                "t2": t2.date().isoformat(),
                "train_rows": train_rows,
                "val_rows": val_rows,
                "test_rows": test_rows,
                "train_fraction": train_rows / total_rows if total_rows else 0.0,
                "val_fraction": val_rows / total_rows if total_rows else 0.0,
                "test_fraction": test_rows / total_rows if total_rows else 0.0,
                "min_split_fraction": min_fraction,
                "ks_train_val": ks_train_val,
                "ks_train_test": ks_train_test,
                "ks_val_test": ks_val_test,
                "meets_min_fraction": min_fraction >= min_split_fraction,
                "meets_ks_threshold": (
                    ks_train_test is not None and ks_train_test < ks_threshold
                ),
            }
        )

        grouped = (
            split_df.groupby(["split_name", "review_stars"], dropna=False)
            .size()
            .reset_index(name="review_count")
        )
        grouped["candidate_id"] = candidate_id
        grouped["review_fraction"] = grouped["review_count"] / grouped.groupby("split_name")["review_count"].transform("sum")
        balance_rows.extend(grouped.to_dict("records"))

    candidate_df = pd.DataFrame(candidate_rows)
    if not candidate_df.empty:
        candidate_df = candidate_df.sort_values(
            ["meets_min_fraction", "meets_ks_threshold", "min_split_fraction", "ks_train_test"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        candidate_df["recommended"] = False
        candidate_df.loc[candidate_df.index[0], "recommended"] = True

    return candidate_df, pd.DataFrame(balance_rows)


def plot_split_comparison(candidate_df: pd.DataFrame, figures: Path) -> None:
    """Plot split fractions and KS drift for each candidate."""
    if candidate_df.empty:
        logger.warning("Candidate split table is empty; skipping Stage 5 figure.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    x = range(len(candidate_df))

    axes[0].bar(x, candidate_df["train_fraction"], label="train", alpha=0.8)
    axes[0].bar(x, candidate_df["val_fraction"], bottom=candidate_df["train_fraction"], label="val", alpha=0.8)
    axes[0].bar(
        x,
        candidate_df["test_fraction"],
        bottom=candidate_df["train_fraction"] + candidate_df["val_fraction"],
        label="test",
        alpha=0.8,
    )
    axes[0].set_xticks(list(x))
    axes[0].set_xticklabels(candidate_df["candidate_id"], rotation=30)
    axes[0].set_ylabel("Fraction of Reviews")
    axes[0].set_title("Track A: Split Size Comparison")
    axes[0].legend()

    axes[1].plot(x, candidate_df["ks_train_test"], marker="o", label="train vs test")
    axes[1].plot(x, candidate_df["ks_train_val"], marker="o", label="train vs val")
    axes[1].plot(x, candidate_df["ks_val_test"], marker="o", label="val vs test")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(candidate_df["candidate_id"], rotation=30)
    axes[1].set_ylabel("KS Statistic")
    axes[1].set_title("Track A: Star Distribution Drift")
    axes[1].legend()

    fig.tight_layout()
    out = figures / "track_a_s5_split_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 5: Split Selection")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    curated = _resolve(config, "curated_dir")
    tables = _resolve(config, "tables_dir")
    figures = _resolve(config, "figures_dir")
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    review_fact_path = curated / "review_fact.parquet"
    split_cfg = config.get("splits", {}).get("candidates", [])
    min_fraction = float(config.get("quality", {}).get("min_split_fraction", 0.10))
    ks_threshold = float(config.get("quality", {}).get("ks_threshold", 0.05))

    con = duckdb.connect()
    try:
        reviews = load_reviews(con, review_fact_path)
    finally:
        con.close()

    candidate_df, balance_df = evaluate_candidates(reviews, split_cfg, min_fraction, ks_threshold)

    candidate_out = tables / "track_a_s5_candidate_splits.parquet"
    candidate_df.to_parquet(candidate_out, index=False)
    logger.info("Wrote %s (%d rows)", candidate_out, len(candidate_df))

    balance_out = tables / "track_a_s5_split_star_balance.parquet"
    balance_df.to_parquet(balance_out, index=False)
    logger.info("Wrote %s (%d rows)", balance_out, len(balance_df))

    plot_split_comparison(candidate_df, figures)
    logger.info("Stage 5 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
