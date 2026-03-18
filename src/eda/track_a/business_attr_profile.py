"""Stage 4: Business attribute completeness profile."""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.common.config import load_config

matplotlib.use("Agg")

logger = logging.getLogger(__name__)


def _resolve(config: dict[str, Any], key: str) -> Path:
    return Path(config["paths"][key])


def _parse_attributes(raw_value: object) -> dict[str, str]:
    """Parse first-level Yelp business attributes into a flat mapping."""
    if raw_value is None:
        return {}

    if isinstance(raw_value, dict):
        payload = raw_value
    else:
        if pd.isna(raw_value):
            return {}
        raw_text = str(raw_value).strip()
        if not raw_text or raw_text.lower() == "null":
            return {}
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            return {}

    flattened: dict[str, str] = {}
    for key, value in payload.items():
        if value in (None, "", "None", "null"):
            continue
        if isinstance(value, (dict, list)):
            flattened[str(key)] = json.dumps(value, sort_keys=True)
        else:
            flattened[str(key)] = str(value)
    return flattened


def load_business_attributes(con: duckdb.DuckDBPyConnection, business_path: Path) -> pd.DataFrame:
    """Load business records and flatten the attributes JSON."""
    base_df = con.execute(
        """
        SELECT
            business_id,
            city,
            categories,
            CAST(attributes AS VARCHAR) AS attributes_json
        FROM read_parquet($1)
        """,
        [str(business_path)],
    ).fetchdf()
    base_df["city"] = base_df["city"].fillna("Unknown")
    base_df["primary_category"] = (
        base_df["categories"].fillna("Unknown").str.split(",").str[0].str.strip()
    )
    base_df["primary_category"] = base_df["primary_category"].replace("", "Unknown")

    attr_df = pd.DataFrame(base_df["attributes_json"].apply(_parse_attributes).tolist())
    if attr_df.empty:
        raise ValueError("No business attributes were available to profile.")

    attr_df = attr_df.where(attr_df.notna(), pd.NA)
    return pd.concat(
        [base_df[["business_id", "city", "primary_category"]], attr_df],
        axis=1,
    )


def summarize_completeness(
    attr_frame: pd.DataFrame,
    group_column: str,
    top_n: int = 15,
) -> pd.DataFrame:
    """Summarize attribute completeness by category or city."""
    attribute_columns = [
        column
        for column in attr_frame.columns
        if column not in {"business_id", "city", "primary_category"}
    ]
    top_groups = attr_frame[group_column].value_counts().head(top_n).index
    filtered = attr_frame[attr_frame[group_column].isin(top_groups)].copy()

    rows: list[dict[str, Any]] = []
    for group_value, group_df in filtered.groupby(group_column):
        business_count = len(group_df)
        for attribute_name in attribute_columns:
            non_null_fraction = float(group_df[attribute_name].notna().mean())
            rows.append(
                {
                    group_column: group_value,
                    "attribute_name": attribute_name,
                    "business_count": business_count,
                    "non_null_fraction": non_null_fraction,
                    "null_rate": 1.0 - non_null_fraction,
                }
            )

    summary = pd.DataFrame(rows)
    if summary.empty:
        return pd.DataFrame(
            columns=[group_column, "attribute_name", "business_count", "non_null_fraction", "null_rate"]
        )
    return summary.sort_values([group_column, "null_rate"], ascending=[True, False])


def plot_null_rate_heatmap(category_summary: pd.DataFrame, figures: Path) -> None:
    """Create a heatmap of attribute null rates for top categories."""
    if category_summary.empty:
        logger.warning("Category completeness summary is empty; skipping heatmap.")
        return

    heatmap_data = (
        category_summary.sort_values(["business_count", "null_rate"], ascending=[False, False])
        .pivot(index="primary_category", columns="attribute_name", values="null_rate")
        .fillna(1.0)
    )
    heatmap_data = heatmap_data.iloc[:12, :20]

    fig, ax = plt.subplots(figsize=(14, 7))
    sns.heatmap(heatmap_data, cmap="mako", vmin=0, vmax=1, ax=ax)
    ax.set_xlabel("Attribute")
    ax.set_ylabel("Primary Category")
    ax.set_title("Track A: Attribute Null Rates by Category")
    fig.tight_layout()
    out = figures / "track_a_s4_attr_null_rate_heatmap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    logger.info("Wrote %s", out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 4: Business Attribute Profile")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)

    curated = _resolve(config, "curated_dir")
    tables = _resolve(config, "tables_dir")
    figures = _resolve(config, "figures_dir")
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    business_path = curated / "business.parquet"

    con = duckdb.connect()
    try:
        attr_frame = load_business_attributes(con, business_path)
    finally:
        con.close()

    category_summary = summarize_completeness(attr_frame, "primary_category")
    city_summary = summarize_completeness(attr_frame, "city")

    category_out = tables / "track_a_s4_attr_completeness_by_category.parquet"
    category_summary.to_parquet(category_out, index=False)
    logger.info("Wrote %s (%d rows)", category_out, len(category_summary))

    city_out = tables / "track_a_s4_attr_completeness_by_city.parquet"
    city_summary.to_parquet(city_out, index=False)
    logger.info("Wrote %s (%d rows)", city_out, len(city_summary))

    plot_null_rate_heatmap(category_summary, figures)
    logger.info("Stage 4 complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    main()
