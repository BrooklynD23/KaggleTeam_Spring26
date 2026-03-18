# Implementation Plan: JSON-to-Database Ingestion, Track A, and Track B Pipelines

**Version:** 1.1
**Date:** 2026-03-11
**Scope:** Data ingestion layer + Track A (Future Star Rating Prediction) + Track B (Usefulness Ranking)

---

## Table of Contents

1. [Part 1: JSON-to-Database Conversion Plan](#part-1-json-to-database-conversion-plan)
2. [Part 2: Track A Pipeline Design](#part-2-track-a-pipeline-design)
3. [Part 3: Track B Pipeline Design](#part-3-track-b-pipeline-design)
4. [Part 4: Shared Infrastructure](#part-4-shared-infrastructure)

---

## Part 1: JSON-to-Database Conversion Plan

### 1.1 Option Evaluation

| Criterion | DuckDB | SQLite + Parquet Staging | Pure Parquet + Polars |
|---|---|---|---|
| **JSON ingestion** | Native `read_json_auto()` with streaming | Requires Python pre-parsing | Polars `scan_ndjson()` with lazy eval |
| **SQL interface** | Full analytical SQL, window functions | Standard SQL, weaker analytics | No SQL; DataFrame API only |
| **Memory management** | Out-of-core by default; configurable memory limit | In-memory for queries; disk for storage | Lazy mode streams; eager mode needs RAM |
| **Parquet I/O** | Native read/write; zero-copy | Requires separate library | Native; very fast |
| **Columnar analytics** | Yes, vectorized engine | Row-oriented; slow for scans | Yes, vectorized |
| **Cross-table joins** | Standard SQL joins | Standard SQL joins | DataFrame joins (less ergonomic for complex multi-table) |
| **4.1 GB handling** | Handles natively, streams from disk | Needs chunked Python loading | Lazy scan handles it; eager will OOM on some entities |
| **Team familiarity** | SQL is universal; Python API is thin | Ubiquitous | Requires Polars-specific knowledge |
| **Persistence** | Single `.duckdb` file or Parquet export | `.sqlite` file | Parquet files on disk |

### 1.2 Recommendation: DuckDB as Primary, Parquet as Exchange Format

**DuckDB** is the recommended primary analytical database for the following reasons:

1. **Native NDJSON ingestion**: `read_ndjson_auto()` handles line-delimited JSON directly from disk without requiring Python-level chunked parsing. This is critical for the 4.1 GB tar.
2. **Out-of-core processing**: DuckDB's buffer manager pages data to disk when memory is constrained, which eliminates OOM risk during joins across the full review table (~7M rows) and user table (~2M rows).
3. **SQL for EDA**: Every pipeline stage can express its logic in SQL, which is more auditable and team-accessible than framework-specific DataFrame code.
4. **Parquet as the persistence layer**: DuckDB reads and writes Parquet natively. The `data/curated/` directory stores Parquet files that any tool (Polars, Pandas, pyarrow) can consume. DuckDB is the query engine, not the storage lock-in.
5. **Window functions for as-of features**: Track A's rolling user/business history and Track B's within-group percentile labels are naturally expressed as SQL window functions.

**Architecture**:
```
tar file
  |
  v
[extract to data/raw/]  -->  NDJSON files on disk
  |
  v
[DuckDB ingestion]      -->  Schema validation + type casting
  |
  v
[DuckDB curated views]  -->  review_fact, review_fact_track_b
  |
  v
[COPY TO Parquet]        -->  data/curated/*.parquet  (portable exchange format)
  |
  v
[Per-stage queries]      -->  outputs/tables/*.parquet, outputs/figures/*.png
```

### 1.3 Extraction Pipeline: tar to JSON to Database

#### Step 1: Extract main JSON tar archive

```bash
# Extract only JSON files from the tar, stripping any directory prefix
mkdir -p data/raw
tar xf "Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar" \
    --directory=data/raw \
    --strip-components=0 \
    '*.json'
```

Expected files after extraction from `yelp_dataset.tar`:

| File | Expected Name | Approx Size | Approx Rows |
|---|---|---|---|
| Business | `yelp_academic_dataset_business.json` | ~120 MB | ~150K |
| Review | `yelp_academic_dataset_review.json` | ~5.5 GB (uncompressed in tar) | ~7M |
| User | `yelp_academic_dataset_user.json` | ~3.4 GB | ~2M |
| Tip | `yelp_academic_dataset_tip.json` | ~200 MB | ~1.2M |
| Checkin | `yelp_academic_dataset_checkin.json` | ~45 MB | ~130K |

**Note**: The tar is 4.1 GB compressed-in-tar. Extracted NDJSON will be larger. Ensure at least 15 GB free disk space.

**Photo scope note**: Photo data is stored separately at `Dataset(Raw)/Yelp Photos/yelp_photos.tar`. Track A and Track B do not require photo data, so photo is explicitly **out of scope for the shared ingestion contract in this plan**. If a future track needs photo, add a second extraction path rather than assuming it is bundled into `yelp_dataset.tar`.

#### Step 2: Validate JSON structure (pre-ingestion)

Before loading into DuckDB, run a lightweight validation pass:

```python
# src/ingest/validate_json_structure.py
import json
from pathlib import Path
from typing import Any

ENTITY_CONFIGS: dict[str, list[str]] = {
    "business": ["business_id", "name", "city", "state", "stars", "review_count", "categories"],
    "review": ["review_id", "user_id", "business_id", "stars", "date", "text", "useful", "funny", "cool"],
    "user": ["user_id", "name", "review_count", "yelping_since", "average_stars", "elite", "fans", "friends"],
    "tip": ["user_id", "business_id", "text", "date", "compliment_count"],
    "checkin": ["business_id", "date"],
}

def validate_first_n_lines(filepath: Path, entity: str, n: int = 100) -> dict[str, Any]:
    """Read the first N lines and verify required keys are present."""
    required_keys = set(ENTITY_CONFIGS[entity])
    missing_keys: list[str] = []
    extra_keys: set[str] = set()
    line_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            record = json.loads(line)
            record_keys = set(record.keys())
            missing = required_keys - record_keys
            if missing:
                missing_keys.append(f"line {i}: {missing}")
            extra_keys |= (record_keys - required_keys)
            line_count = i + 1

    return {
        "entity": entity,
        "lines_checked": line_count,
        "missing_key_issues": missing_keys,
        "extra_keys_observed": sorted(extra_keys),
        "status": "PASS" if len(missing_keys) == 0 else "FAIL",
    }
```

#### Step 3: DuckDB ingestion with schema enforcement

```python
# src/ingest/load_to_duckdb.py
import duckdb
from pathlib import Path

def create_yelp_database(raw_dir: Path, db_path: Path) -> None:
    """Load all Yelp NDJSON files into a DuckDB database with typed schemas."""
    con = duckdb.connect(str(db_path))

    # Set memory limit to avoid crowding the machine
    con.execute("SET memory_limit='4GB'")
    con.execute("SET threads TO 4")

    # --- Business ---
    con.execute("""
        CREATE OR REPLACE TABLE business AS
        SELECT
            business_id::VARCHAR        AS business_id,
            name::VARCHAR               AS name,
            address::VARCHAR            AS address,
            city::VARCHAR               AS city,
            state::VARCHAR              AS state,
            postal_code::VARCHAR        AS postal_code,
            latitude::DOUBLE            AS latitude,
            longitude::DOUBLE           AS longitude,
            stars::DOUBLE               AS stars,
            review_count::INTEGER       AS review_count,
            is_open::INTEGER            AS is_open,
            attributes::JSON            AS attributes,
            categories::VARCHAR         AS categories,
            hours::JSON                 AS hours
        FROM read_ndjson_auto('{raw_dir}/yelp_academic_dataset_business.json')
    """.format(raw_dir=raw_dir))

    # --- Review ---
    con.execute("""
        CREATE OR REPLACE TABLE review AS
        SELECT
            review_id::VARCHAR          AS review_id,
            user_id::VARCHAR            AS user_id,
            business_id::VARCHAR        AS business_id,
            stars::DOUBLE               AS stars,
            date::DATE                  AS review_date,
            text::VARCHAR               AS text,
            useful::INTEGER             AS useful,
            funny::INTEGER              AS funny,
            cool::INTEGER               AS cool
        FROM read_ndjson_auto('{raw_dir}/yelp_academic_dataset_review.json')
    """.format(raw_dir=raw_dir))

    # --- User ---
    con.execute("""
        CREATE OR REPLACE TABLE "user" AS
        SELECT
            user_id::VARCHAR            AS user_id,
            name::VARCHAR               AS name,
            review_count::INTEGER       AS review_count,
            yelping_since::DATE         AS yelping_since,
            useful::INTEGER             AS useful,
            funny::INTEGER              AS funny,
            cool::INTEGER               AS cool,
            elite::VARCHAR              AS elite,
            friends::VARCHAR            AS friends,
            fans::INTEGER               AS fans,
            average_stars::DOUBLE       AS average_stars,
            compliment_hot::INTEGER     AS compliment_hot,
            compliment_more::INTEGER    AS compliment_more,
            compliment_profile::INTEGER AS compliment_profile,
            compliment_cute::INTEGER    AS compliment_cute,
            compliment_list::INTEGER    AS compliment_list,
            compliment_note::INTEGER    AS compliment_note,
            compliment_plain::INTEGER   AS compliment_plain,
            compliment_cool::INTEGER    AS compliment_cool,
            compliment_funny::INTEGER   AS compliment_funny,
            compliment_writer::INTEGER  AS compliment_writer,
            compliment_photos::INTEGER  AS compliment_photos
        FROM read_ndjson_auto('{raw_dir}/yelp_academic_dataset_user.json')
    """.format(raw_dir=raw_dir))

    # --- Tip ---
    con.execute("""
        CREATE OR REPLACE TABLE tip AS
        SELECT
            user_id::VARCHAR            AS user_id,
            business_id::VARCHAR        AS business_id,
            text::VARCHAR               AS text,
            date::DATE                  AS tip_date,
            compliment_count::INTEGER   AS compliment_count
        FROM read_ndjson_auto('{raw_dir}/yelp_academic_dataset_tip.json')
    """.format(raw_dir=raw_dir))

    # --- Checkin ---
    con.execute("""
        CREATE OR REPLACE TABLE checkin AS
        SELECT
            business_id::VARCHAR        AS business_id,
            date::VARCHAR               AS checkin_dates
        FROM read_ndjson_auto('{raw_dir}/yelp_academic_dataset_checkin.json')
    """.format(raw_dir=raw_dir))

    con.close()
```

**Photo note**: Do not load `photo` in this shared module. If photo is needed later, create a separate ingestion module that extracts `Dataset(Raw)/Yelp Photos/yelp_photos.tar` into its own raw directory and materializes `photo` outside the Track A/B contract.

#### Step 4: Row-count validation and data quality checks

```python
# src/validate/schema_checks.py
import duckdb
from dataclasses import dataclass

@dataclass(frozen=True)
class EntityReport:
    entity: str
    row_count: int
    null_rates: dict[str, float]
    min_date: str | None
    max_date: str | None
    status: str

def run_quality_checks(db_path: str) -> list[EntityReport]:
    """Run row counts, null rates, and date range checks on all entities."""
    con = duckdb.connect(db_path, read_only=True)
    reports: list[EntityReport] = []

    checks = {
        "business": {
            "key_cols": ["business_id", "city", "state", "stars"],
            "date_col": None,
        },
        "review": {
            "key_cols": ["review_id", "user_id", "business_id", "stars", "review_date", "text"],
            "date_col": "review_date",
        },
        "user": {
            "key_cols": ["user_id", "review_count", "yelping_since", "average_stars"],
            "date_col": "yelping_since",
        },
        "tip": {
            "key_cols": ["user_id", "business_id", "text", "tip_date"],
            "date_col": "tip_date",
        },
        "checkin": {
            "key_cols": ["business_id", "checkin_dates"],
            "date_col": None,
        },
    }

    for entity, cfg in checks.items():
        table_name = f'"{entity}"' if entity == "user" else entity
        row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        # Null rates for key columns
        null_exprs = [
            f"ROUND(SUM(CASE WHEN {col} IS NULL THEN 1 ELSE 0 END)::DOUBLE / COUNT(*), 4) AS {col}_null_rate"
            for col in cfg["key_cols"]
        ]
        null_query = f"SELECT {', '.join(null_exprs)} FROM {table_name}"
        null_row = con.execute(null_query).fetchone()
        null_rates = {
            cfg["key_cols"][i]: float(null_row[i])
            for i in range(len(cfg["key_cols"]))
        }

        # Date range
        min_date, max_date = None, None
        if cfg["date_col"]:
            date_row = con.execute(
                f"SELECT MIN({cfg['date_col']})::VARCHAR, MAX({cfg['date_col']})::VARCHAR FROM {table_name}"
            ).fetchone()
            min_date, max_date = date_row[0], date_row[1]

        # Status: FAIL if any key column has >1% nulls
        status = "PASS" if all(v < 0.01 for v in null_rates.values()) else "WARN"

        reports.append(EntityReport(
            entity=entity,
            row_count=row_count,
            null_rates=null_rates,
            min_date=min_date,
            max_date=max_date,
            status=status,
        ))

    con.close()
    return reports
```

**Expected validation output:**

| Entity | Expected Rows | Key Null Check | Date Range |
|---|---|---|---|
| business | ~150,000 | business_id: 0% | N/A |
| review | ~7,000,000 | review_id: 0%, stars: 0% | ~2005 to ~2022 |
| user | ~2,000,000 | user_id: 0% | yelping_since: ~2004 to ~2022 |
| tip | ~1,200,000 | user_id: 0% | ~2010 to ~2022 |
| checkin | ~130,000 | business_id: 0% | N/A (comma-separated string) |

#### Step 5: Export curated Parquet files

```sql
-- Run inside DuckDB after validation passes
COPY business TO 'data/curated/business.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
COPY review TO 'data/curated/review.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
COPY "user" TO 'data/curated/user.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
COPY tip TO 'data/curated/tip.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
COPY checkin TO 'data/curated/checkin.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

### 1.4 Memory Management Strategy

The review and user NDJSON files are the two largest entities. DuckDB handles these via streaming ingestion, but explicit safeguards are still needed:

1. **DuckDB memory cap**: Set `SET memory_limit='4GB'` to prevent DuckDB from consuming all available RAM. It will spill to disk transparently.
2. **Thread control**: Set `SET threads TO 4` (adjust based on machine) to limit parallel scan pressure.
3. **Do not load review text into memory outside DuckDB**: Python-side operations on review text (e.g., word count) should use DuckDB SQL (`LENGTH(text)`, `REGEXP_SPLIT_TO_ARRAY`) rather than pulling 7M text strings into a Pandas DataFrame.
4. **Parquet compression**: ZSTD compression reduces curated files to roughly 30-40% of raw NDJSON size, making downstream reads faster.
5. **Chunked Python fallback**: If any step requires Pandas/Polars outside DuckDB (e.g., matplotlib plotting), read Parquet with column projection and row filters:

```python
import polars as pl

# Only read the columns and rows needed for a specific stage
df = pl.scan_parquet("data/curated/review.parquet").select(
    ["review_date", "stars", "useful"]
).filter(
    pl.col("review_date").is_not_null()
).collect()
```

### 1.5 Entity Schema Definitions

#### business

| Column | Type | Nullable | Notes |
|---|---|---|---|
| business_id | VARCHAR | No | Primary key (22-char Yelp hash) |
| name | VARCHAR | No | |
| address | VARCHAR | Yes | |
| city | VARCHAR | No | |
| state | VARCHAR | No | Two-letter code |
| postal_code | VARCHAR | Yes | |
| latitude | DOUBLE | Yes | |
| longitude | DOUBLE | Yes | |
| stars | DOUBLE | No | **CAUTION: Lifetime aggregate -- leaks future for Track A** |
| review_count | INTEGER | No | **CAUTION: Lifetime aggregate** |
| is_open | INTEGER | No | 0 or 1; snapshot field, Track B only |
| attributes | JSON | Yes | Nested key-value pairs; needs flattening |
| categories | VARCHAR | Yes | Comma-separated string |
| hours | JSON | Yes | Day-of-week: "HH:MM-HH:MM" |

#### review

| Column | Type | Nullable | Notes |
|---|---|---|---|
| review_id | VARCHAR | No | Primary key |
| user_id | VARCHAR | No | FK to user |
| business_id | VARCHAR | No | FK to business |
| stars | DOUBLE | No | 1.0 to 5.0 in 1.0 increments; **this is the Track A target** |
| review_date | DATE | No | Temporal key for all as-of logic |
| text | VARCHAR | No | Full review text; never display raw in outputs |
| useful | INTEGER | No | Non-negative; **this is the Track B target signal** |
| funny | INTEGER | No | Non-negative; raw-only field, excluded from curated Track A/B tables |
| cool | INTEGER | No | Non-negative; raw-only field, excluded from curated Track A/B tables |

#### user

| Column | Type | Nullable | Notes |
|---|---|---|---|
| user_id | VARCHAR | No | Primary key |
| name | VARCHAR | No | Display name (pseudonymous) |
| review_count | INTEGER | No | **CAUTION: Lifetime aggregate** |
| yelping_since | DATE | No | Account creation date |
| useful | INTEGER | No | Lifetime total useful votes received |
| funny | INTEGER | No | Lifetime total |
| cool | INTEGER | No | Lifetime total |
| elite | VARCHAR | Yes | Comma-separated years, e.g., "2015,2016,2017"; snapshot field, Track B only |
| friends | VARCHAR | Yes | Comma-separated user_ids |
| fans | INTEGER | No | Snapshot field, Track B only |
| average_stars | DOUBLE | No | **CAUTION: Lifetime aggregate -- leaks future for Track A** |
| compliment_* | INTEGER | No | 11 compliment type columns |

#### tip

| Column | Type | Nullable | Notes |
|---|---|---|---|
| user_id | VARCHAR | No | FK to user |
| business_id | VARCHAR | No | FK to business |
| text | VARCHAR | No | Short tip text |
| tip_date | DATE | No | |
| compliment_count | INTEGER | No | |

#### checkin

| Column | Type | Nullable | Notes |
|---|---|---|---|
| business_id | VARCHAR | No | FK to business |
| checkin_dates | VARCHAR | No | Comma-separated timestamps; needs parsing |

**Excluded from this plan**: `photo` is intentionally omitted from the shared A/B ingestion schema because it is stored in a separate raw archive and neither Track A nor Track B depends on it.

---

## Part 2: Track A Pipeline Design

### 2.1 review_fact Construction (Shared Stage 0)

The curated layer is intentionally split into two objects:

1. `review_fact`: a **Track A-safe base table** that only contains fields acceptable for strict as-of analysis.
2. `review_fact_track_b`: a **Track B snapshot view** that adds snapshot-only fields (`is_open`, `fans`, `elite`) because Track B is explicitly a single-snapshot task.

```sql
-- src/curate/build_review_fact.sql (executed via Python wrapper)
CREATE OR REPLACE TABLE review_fact AS
SELECT
    r.review_id,
    r.user_id,
    r.business_id,
    r.stars         AS review_stars,
    r.review_date,
    r.useful,
    LENGTH(r.text)  AS text_char_count,
    ARRAY_LENGTH(STRING_SPLIT(TRIM(r.text), ' ')) AS text_word_count,

    -- Business fields retained in the Track A-safe base table
    b.city,
    b.state,
    b.categories,
    b.latitude,
    b.longitude,

    -- User fields retained in the Track A-safe base table
    u.yelping_since,

    -- Derived temporal keys
    EXTRACT(YEAR FROM r.review_date)  AS review_year,
    EXTRACT(MONTH FROM r.review_date) AS review_month,
    DATEDIFF('day', u.yelping_since, r.review_date) AS user_tenure_days

FROM review r
JOIN business b ON r.business_id = b.business_id
JOIN "user" u ON r.user_id = u.user_id
WHERE r.review_date IS NOT NULL
  AND r.stars IS NOT NULL;

CREATE OR REPLACE VIEW review_fact_track_b AS
SELECT
    rf.*,
    b.is_open,
    u.fans,
    u.elite
FROM review_fact rf
JOIN business b ON rf.business_id = b.business_id
JOIN "user" u ON rf.user_id = u.user_id;
```

**Critical design decisions:**

1. **Track A-safe base table**: `review_fact` excludes lifetime aggregates and snapshot-only fields that are not safe under strict as-of semantics. In particular, `business.stars`, `business.review_count`, `business.is_open`, `user.average_stars`, `user.review_count`, `user.fans`, and `user.elite` must not appear in the Track A base table.
2. **Track B snapshot extension**: `review_fact_track_b` is the place where Track B may intentionally use snapshot-only fields. Track A must never read from this view.
3. **Text is summarized, not carried**: `text_char_count` and `text_word_count` are derived at join time. The raw `text` column is not included in curated tables to keep outputs aggregate-safe. If a stage needs raw text (e.g., sentiment proxy), it reads from `review.parquet` directly, filtered by review_id.
4. **JOIN type and row-loss gate**: INNER JOIN is used. Any review without a matching business or user is dropped. This is acceptable only if row loss stays below a configured threshold; otherwise the pipeline must stop.

**Validation query:**

```sql
-- Row count match
SELECT
    (SELECT COUNT(*) FROM review) AS raw_review_count,
    (SELECT COUNT(*) FROM review_fact) AS fact_count,
    (SELECT COUNT(*) FROM review) - (SELECT COUNT(*) FROM review_fact) AS dropped_rows;
```

If `dropped_rows / raw_review_count > quality.review_fact_max_row_loss_fraction`, stop the pipeline and require explicit review. If row loss is non-zero but within threshold, log the orphan `review_id` values and their missing foreign keys before continuing.

### 2.2 Stage 1: Temporal Profile

**Objective**: Profile star distribution and review volume over time to inform split selection.

**SQL for key output:**

```sql
-- Star distribution by year-month
SELECT
    review_year,
    review_month,
    review_stars,
    COUNT(*)        AS review_count,
    AVG(review_stars) AS mean_stars
FROM review_fact
GROUP BY review_year, review_month, review_stars
ORDER BY review_year, review_month, review_stars;
```

```sql
-- Monthly volume time series
SELECT
    DATE_TRUNC('month', review_date) AS month,
    COUNT(*) AS review_count,
    AVG(review_stars) AS mean_stars,
    STDDEV(review_stars) AS std_stars
FROM review_fact
GROUP BY DATE_TRUNC('month', review_date)
ORDER BY month;
```

**Visualization logic** (Python with matplotlib):
- Line plot of monthly review count (left y-axis) and mean star rating (right y-axis).
- Stacked bar chart of star distribution (1-5) by year, normalized to percentage.

**Output artifacts:**
- `outputs/tables/track_a_s1_stars_by_year_month.parquet`
- `outputs/tables/track_a_s1_review_volume_by_period.parquet`
- `outputs/figures/track_a_s1_star_distribution_over_time.png`
- `outputs/figures/track_a_s1_review_volume_timeline.png`

### 2.3 Stage 2: Text Profile

**Objective**: Characterize text length distributions by star rating.

```sql
-- Text length statistics by star rating
SELECT
    review_stars,
    COUNT(*) AS n,
    AVG(text_word_count) AS mean_words,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY text_word_count) AS median_words,
    STDDEV(text_word_count) AS std_words,
    MIN(text_word_count) AS min_words,
    MAX(text_word_count) AS max_words
FROM review_fact
GROUP BY review_stars
ORDER BY review_stars;
```

**Sentiment proxy**: Rather than pulling all 7M text records into Python, compute a sampled sentiment pass:

```python
import duckdb
from textblob import TextBlob

con = duckdb.connect("data/yelp.duckdb", read_only=True)

# Sample 50K reviews stratified by star rating (10K per star)
sample = con.execute("""
    SELECT review_id, review_stars, text
    FROM review
    USING SAMPLE 50000 ROWS (SYSTEM, 42)
""").fetchdf()

sample["polarity"] = sample["text"].apply(lambda t: TextBlob(t).sentiment.polarity)
# Aggregate: do not store raw text in output
sentiment_summary = sample.groupby("review_stars")["polarity"].describe()
```

### 2.4 Stage 3: User History Profile (As-Of Feature Computation)

This is the most computationally demanding EDA stage. It computes, for each review, the user's prior review statistics at the time of that review.

**Strategy: day-level preaggregation plus cumulative windows**

```sql
-- Step 1: compress each user to one row per date to avoid inventing same-day order
CREATE OR REPLACE TABLE user_day_stats AS
SELECT
    user_id,
    review_date,
    COUNT(*) AS reviews_on_day,
    SUM(review_stars) AS stars_sum_on_day,
    SUM(review_stars * review_stars) AS stars_sq_sum_on_day
FROM review_fact
GROUP BY user_id, review_date;

CREATE OR REPLACE TABLE user_day_history AS
SELECT
    user_id,
    review_date,
    COALESCE(SUM(reviews_on_day) OVER (
        PARTITION BY user_id
        ORDER BY review_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ), 0) AS user_prior_review_count,
    SUM(stars_sum_on_day) OVER (
        PARTITION BY user_id
        ORDER BY review_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS user_prior_stars_sum,
    SUM(stars_sq_sum_on_day) OVER (
        PARTITION BY user_id
        ORDER BY review_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS user_prior_stars_sq_sum
FROM user_day_stats;

-- Step 2: attach the same prior-history values to every review on the same date
CREATE OR REPLACE TABLE user_history_asof AS
SELECT
    rf.review_id,
    rf.user_id,
    rf.review_date,
    rf.review_stars,
    udh.user_prior_review_count,
    CASE
        WHEN udh.user_prior_review_count > 0
        THEN udh.user_prior_stars_sum / udh.user_prior_review_count
    END AS user_prior_avg_stars,
    CASE
        WHEN udh.user_prior_review_count > 1 THEN SQRT(
            (
                udh.user_prior_stars_sq_sum
                - POWER(udh.user_prior_stars_sum, 2) / udh.user_prior_review_count
            ) / (udh.user_prior_review_count - 1)
        )
    END AS user_prior_std_stars
FROM review_fact rf
LEFT JOIN user_day_history udh
    ON rf.user_id = udh.user_id
   AND rf.review_date = udh.review_date;
```

**Why this is correct**: the dataset exposes dates, not timestamps. Every review written by the same user on the same date therefore receives the same prior-history features, which uses only strictly earlier dates and avoids fabricated intra-day order.

**Equivalent approach for business history:**

```sql
CREATE OR REPLACE TABLE business_day_stats AS
SELECT
    business_id,
    review_date,
    COUNT(*) AS reviews_on_day,
    SUM(review_stars) AS stars_sum_on_day,
    SUM(review_stars * review_stars) AS stars_sq_sum_on_day
FROM review_fact
GROUP BY business_id, review_date;

CREATE OR REPLACE TABLE business_day_history AS
SELECT
    business_id,
    review_date,
    COALESCE(SUM(reviews_on_day) OVER (
        PARTITION BY business_id
        ORDER BY review_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ), 0) AS biz_prior_review_count,
    SUM(stars_sum_on_day) OVER (
        PARTITION BY business_id
        ORDER BY review_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS biz_prior_stars_sum,
    SUM(stars_sq_sum_on_day) OVER (
        PARTITION BY business_id
        ORDER BY review_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS biz_prior_stars_sq_sum
FROM business_day_stats;

CREATE OR REPLACE TABLE business_history_asof AS
SELECT
    rf.review_id,
    rf.business_id,
    rf.review_date,
    rf.review_stars,
    bdh.biz_prior_review_count,
    CASE
        WHEN bdh.biz_prior_review_count > 0
        THEN bdh.biz_prior_stars_sum / bdh.biz_prior_review_count
    END AS biz_prior_avg_stars,
    CASE
        WHEN bdh.biz_prior_review_count > 1 THEN SQRT(
            (
                bdh.biz_prior_stars_sq_sum
                - POWER(bdh.biz_prior_stars_sum, 2) / bdh.biz_prior_review_count
            ) / (bdh.biz_prior_review_count - 1)
        )
    END AS biz_prior_std_stars
FROM review_fact rf
LEFT JOIN business_day_history bdh
    ON rf.business_id = bdh.business_id
   AND rf.review_date = bdh.review_date;
```

**EDA profiling queries on the as-of tables:**

```sql
-- Distribution of user prior review counts at review time
SELECT
    CASE
        WHEN user_prior_review_count = 0 THEN '0 (first review)'
        WHEN user_prior_review_count BETWEEN 1 AND 4 THEN '1-4'
        WHEN user_prior_review_count BETWEEN 5 AND 19 THEN '5-19'
        WHEN user_prior_review_count BETWEEN 20 AND 99 THEN '20-99'
        ELSE '100+'
    END AS history_depth_bucket,
    COUNT(*) AS review_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM user_history_asof
GROUP BY 1
ORDER BY MIN(COALESCE(user_prior_review_count, 0));
```

**Output artifacts:**
- `outputs/tables/track_a_s3_user_history_depth.parquet`
- `outputs/figures/track_a_s3_user_prior_review_count_dist.png` (CDF plot)
- `outputs/figures/track_a_s3_user_tenure_vs_rating_var.png` (scatter: tenure vs. prior_std_stars)

### 2.5 Stage 4: Business Attribute Profile

**Objective**: Assess how complete business attributes are, since they are potential features.

```sql
-- Flatten the top-level keys of the attributes JSON
-- DuckDB can extract JSON keys dynamically
SELECT
    json_keys(attributes) AS attr_keys
FROM business
WHERE attributes IS NOT NULL
LIMIT 1;
```

For a known set of common attributes (discovered from the first query), compute null rates:

```sql
-- Example for known attribute keys
SELECT
    COUNT(*) AS total_businesses,
    SUM(CASE WHEN attributes->>'RestaurantsPriceRange2' IS NOT NULL THEN 1 ELSE 0 END) AS has_price_range,
    SUM(CASE WHEN attributes->>'WiFi' IS NOT NULL THEN 1 ELSE 0 END) AS has_wifi,
    SUM(CASE WHEN attributes->>'GoodForKids' IS NOT NULL THEN 1 ELSE 0 END) AS has_good_for_kids,
    SUM(CASE WHEN attributes->>'RestaurantsReservations' IS NOT NULL THEN 1 ELSE 0 END) AS has_reservations,
    SUM(CASE WHEN attributes->>'BikeParking' IS NOT NULL THEN 1 ELSE 0 END) AS has_bike_parking
FROM business;
```

**Category-level breakdown:**

```sql
-- Null rate of price_range by primary category
WITH biz_with_cat AS (
    SELECT
        business_id,
        TRIM(SPLIT_PART(categories, ',', 1)) AS primary_category,
        attributes->>'RestaurantsPriceRange2' AS price_range
    FROM business
    WHERE categories IS NOT NULL
)
SELECT
    primary_category,
    COUNT(*) AS n,
    ROUND(SUM(CASE WHEN price_range IS NULL THEN 1 ELSE 0 END)::DOUBLE / COUNT(*), 3) AS null_rate
FROM biz_with_cat
GROUP BY primary_category
HAVING COUNT(*) >= 100
ORDER BY null_rate DESC;
```

### 2.6 Stage 5: Temporal Split Selection

**Methodology**: Use review date quantiles to propose candidate splits, then validate each candidate for distribution stability.

```sql
-- Compute date percentiles for split candidates
SELECT
    PERCENTILE_CONT(0.60) WITHIN GROUP (ORDER BY review_date) AS p60,
    PERCENTILE_CONT(0.65) WITHIN GROUP (ORDER BY review_date) AS p65,
    PERCENTILE_CONT(0.70) WITHIN GROUP (ORDER BY review_date) AS p70,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY review_date) AS p75,
    PERCENTILE_CONT(0.80) WITHIN GROUP (ORDER BY review_date) AS p80,
    PERCENTILE_CONT(0.85) WITHIN GROUP (ORDER BY review_date) AS p85,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY review_date) AS p90
FROM review_fact;
```

**Candidate split evaluation:**

For each candidate pair (T1, T2), compute:

```sql
-- Parameterized for a given T1, T2
WITH split_labels AS (
    SELECT
        review_stars,
        CASE
            WHEN review_date < :t1 THEN 'train'
            WHEN review_date < :t2 THEN 'val'
            ELSE 'test'
        END AS split
    FROM review_fact
)
SELECT
    split,
    review_stars,
    COUNT(*) AS n,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY split), 2) AS pct_within_split
FROM split_labels
GROUP BY split, review_stars
ORDER BY split, review_stars;
```

**KS test for distribution shift** (Python):

```python
from scipy import stats
import duckdb

con = duckdb.connect("data/yelp.duckdb", read_only=True)

train_stars = con.execute(
    "SELECT review_stars FROM review_fact WHERE review_date < ?", [t1]
).fetchnumpy()["review_stars"]

test_stars = con.execute(
    "SELECT review_stars FROM review_fact WHERE review_date >= ?", [t2]
).fetchnumpy()["review_stars"]

ks_stat, ks_pvalue = stats.ks_2samp(train_stars, test_stars)
# Pass criterion: ks_stat < 0.05
```

**Recommended starting candidates** (from PRD guidance):

| Candidate | T1 Percentile | T2 Percentile | Rationale |
|---|---|---|---|
| A | 65th | 82nd | More training data, moderate val |
| B | 70th | 85th | PRD default recommendation |
| C | 70th | 90th | Smaller test set, longer val window |
| D | 75th | 88th | Less training data, tests on most recent reviews |

Select the candidate where:
1. KS statistic between train and test star distributions is minimized.
2. Each split has at least 10% of total reviews.
3. Val and test each have at least 500K reviews (for stable evaluation).

### 2.7 Stage 6: Leakage Audit Implementation

```python
# src/validate/leakage_audit.py
import duckdb
from dataclasses import dataclass

@dataclass(frozen=True)
class LeakageCheckResult:
    check_name: str
    severity: str  # CRITICAL, WARNING, INFO
    flagged_count: int
    detail: str
    status: str  # PASS, FAIL, WARN

def run_track_a_leakage_audit(db_path: str, t1: str, t2: str) -> list[LeakageCheckResult]:
    """Run all Track A leakage checks and return results."""
    con = duckdb.connect(db_path, read_only=True)
    results: list[LeakageCheckResult] = []

    # Check 1: Track A-safe curated table does not expose banned columns
    banned_cols = con.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'review_fact'
          AND column_name IN (
              'stars', 'review_count', 'average_stars', 'is_open', 'fans', 'elite'
          )
        ORDER BY column_name
    """).fetchall()
    banned_col_names = [row[0] for row in banned_cols]

    results.append(LeakageCheckResult(
        check_name="track_a_banned_columns_absent",
        severity="CRITICAL",
        flagged_count=len(banned_col_names),
        detail=(
            "review_fact must exclude lifetime aggregates and snapshot-only fields "
            f"that are not Track A-safe. Found banned columns: {banned_col_names}"
        ),
        status="FAIL" if banned_col_names else "PASS",
    ))

    # Check 2: Same user-business pair across train and test
    overlap = con.execute(f"""
        SELECT COUNT(DISTINCT user_id || '::' || business_id) AS overlap_pairs
        FROM review_fact
        WHERE user_id || '::' || business_id IN (
            SELECT user_id || '::' || business_id
            FROM review_fact
            WHERE review_date < '{t1}'
        )
        AND review_date >= '{t2}'
    """).fetchone()[0]

    results.append(LeakageCheckResult(
        check_name="user_business_pair_train_test_overlap",
        severity="WARNING",
        flagged_count=overlap,
        detail=(
            f"{overlap} user-business pairs appear in both train (<{t1}) and test (>={t2}). "
            "Consider whether to allow repeat visits or exclude them."
        ),
        status="WARN" if overlap > 0 else "PASS",
    ))

    # Check 3: Verify as-of tables use only strictly earlier dates
    future_leak = con.execute(f"""
        SELECT COUNT(*)
        FROM user_history_asof uha
        JOIN review_fact rf ON uha.review_id = rf.review_id
        WHERE uha.user_prior_review_count > (
            SELECT COUNT(*)
            FROM review_fact rf2
            WHERE rf2.user_id = rf.user_id
              AND rf2.review_date < rf.review_date
        )
    """).fetchone()[0]

    results.append(LeakageCheckResult(
        check_name="asof_user_history_future_leak",
        severity="CRITICAL",
        flagged_count=future_leak,
        detail=(
            f"{future_leak} rows where as-of user prior count exceeds "
            "the actual count of strictly earlier-date reviews. Should be 0."
        ),
        status="FAIL" if future_leak > 0 else "PASS",
    ))

    con.close()
    return results
```

### 2.8 Stage 7: Feature Availability Matrix

```sql
-- Feature availability report
WITH feature_checks AS (
    SELECT
        rf.review_id,
        CASE
            WHEN rf.review_date < :t1 THEN 'train'
            WHEN rf.review_date < :t2 THEN 'val'
            ELSE 'test'
        END AS split,

        -- Text features: always available
        CASE WHEN rf.text_word_count IS NOT NULL THEN 1 ELSE 0 END AS has_text_length,

        -- User as-of features
        CASE WHEN uha.user_prior_review_count IS NOT NULL
              AND uha.user_prior_review_count > 0 THEN 1 ELSE 0 END AS has_user_history,

        -- Business as-of features
        CASE WHEN bha.biz_prior_review_count IS NOT NULL
              AND bha.biz_prior_review_count > 0 THEN 1 ELSE 0 END AS has_biz_history,

        -- User tenure
        CASE WHEN rf.user_tenure_days IS NOT NULL THEN 1 ELSE 0 END AS has_user_tenure,

        -- Business city
        CASE WHEN rf.city IS NOT NULL THEN 1 ELSE 0 END AS has_city,

        -- Business categories
        CASE WHEN rf.categories IS NOT NULL THEN 1 ELSE 0 END AS has_categories

    FROM review_fact rf
    LEFT JOIN user_history_asof uha ON rf.review_id = uha.review_id
    LEFT JOIN business_history_asof bha ON rf.review_id = bha.review_id
)
SELECT
    split,
    COUNT(*) AS total_reviews,
    ROUND(AVG(has_text_length), 4) AS text_length_coverage,
    ROUND(AVG(has_user_history), 4) AS user_history_coverage,
    ROUND(AVG(has_biz_history), 4) AS biz_history_coverage,
    ROUND(AVG(has_user_tenure), 4) AS user_tenure_coverage,
    ROUND(AVG(has_city), 4) AS city_coverage,
    ROUND(AVG(has_categories), 4) AS categories_coverage
FROM feature_checks
GROUP BY split
ORDER BY CASE split WHEN 'train' THEN 1 WHEN 'val' THEN 2 ELSE 3 END;
```

**Expected insight**: `has_user_history` coverage will be lower in the train split (more first-time reviewers early in the dataset's life) and higher in val/test (users have accumulated history). This is not leakage -- it reflects genuine data availability.

### 2.9 Stage 8: Summary Report

Automated markdown generation that pulls key metrics from all prior stages:

```python
# src/eda/track_a/summary_report.py
def generate_summary(output_dir: str, config: dict) -> str:
    """Generate the Track A EDA summary report as markdown."""
    sections = [
        "# Track A EDA Summary Report\n",
        f"**Generated:** {datetime.now().isoformat()}\n",
        "## 1. Dataset Overview",
        _load_row_counts(output_dir),
        "## 2. Temporal Profile",
        _load_temporal_findings(output_dir),
        "## 3. Text Profile",
        _load_text_findings(output_dir),
        "## 4. User History Availability",
        _load_user_history_findings(output_dir),
        "## 5. Business Attribute Completeness",
        _load_attribute_findings(output_dir),
        "## 6. Temporal Split Decision",
        _load_split_decision(output_dir),
        "## 7. Leakage Audit Results",
        _load_leakage_results(output_dir),
        "## 8. Feature Availability Matrix",
        _load_feature_matrix(output_dir),
        "## 9. Recommendations for Modeling",
        _generate_recommendations(),
    ]
    return "\n\n".join(sections)
```

### 2.10 Track A Stage Dependency Graph

```
Stage 0 (shared): ingest + validate + build_review_fact
    |
    +--> Stage 1: temporal_profile
    |       |
    +--> Stage 2: text_profile
    |
    +--> Stage 3: user_history_profile  (builds user_history_asof, business_history_asof)
    |
    +--> Stage 4: business_attr_profile
    |
    +--- All of 1-4 feed into:
            |
            v
         Stage 5: split_selection  (depends on Stage 1 volume data)
            |
            v
         Stage 6: leakage_audit  (depends on Stage 3 as-of tables + Stage 5 split)
            |
            v
         Stage 7: feature_availability  (depends on Stage 3 + Stage 5)
            |
            v
         Stage 8: summary_report  (depends on all prior stages)
```

**Parallelism opportunity**: Stages 1, 2, 3, and 4 can run in parallel after Stage 0 completes. Stage 5 needs Stage 1. Stages 6 and 7 need Stages 3 and 5. Stage 8 is strictly sequential after all others.

---

## Part 3: Track B Pipeline Design

### 3.1 Snapshot Reference Date Determination

Track B operates on a single dataset snapshot. The `snapshot_reference_date` is the date at which we consider the `useful` vote counts to be "observed." Since the Yelp dataset does not include a release date, Stage 0 computes this once and materializes it in `data/curated/snapshot_metadata.json`. Track B uses `review_fact_track_b`, the snapshot-enriched view built specifically for this snapshot task, plus the snapshot manifest.

**Stage 0 computation:**

```sql
SELECT GREATEST(
  (SELECT MAX(review_date) FROM review),
  (SELECT MAX(tip_date) FROM tip)
) AS snapshot_reference_date;
```

**Materialized manifest contract:**
- Write `data/curated/snapshot_metadata.json` during the shared curation stage.
- Required fields: `snapshot_reference_date`, `dataset_release_tag`.
- Optional provenance field: `computed_from`.
- All Track B stages read this file; they do not independently re-infer the snapshot date.

```json
{
  "snapshot_reference_date": "2022-01-19",
  "dataset_release_tag": "yelp_academic_2022",
  "computed_from": "MAX(review_date, tip_date)"
}
```

### 3.2 Stage 1: Usefulness Vote Distribution

```sql
-- Overall useful vote distribution
SELECT
    useful,
    COUNT(*) AS review_count
FROM review_fact_track_b
GROUP BY useful
ORDER BY useful;

-- Bucket summary for visualization
SELECT
    CASE
        WHEN useful = 0 THEN '0'
        WHEN useful = 1 THEN '1'
        WHEN useful BETWEEN 2 AND 4 THEN '2-4'
        WHEN useful BETWEEN 5 AND 9 THEN '5-9'
        WHEN useful BETWEEN 10 AND 24 THEN '10-24'
        WHEN useful BETWEEN 25 AND 99 THEN '25-99'
        ELSE '100+'
    END AS useful_bucket,
    COUNT(*) AS n,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct
FROM review_fact_track_b
GROUP BY 1
ORDER BY MIN(useful);
```

**Expected findings:**
- ~60-70% of reviews have `useful = 0` (severe zero inflation).
- Long tail: a small number of reviews have 50+ useful votes.
- This confirms that raw useful counts are not suitable as a regression target without transformation.

**Category-level zero fraction:**

```sql
SELECT
    TRIM(SPLIT_PART(categories, ',', 1)) AS primary_category,
    COUNT(*) AS n,
    ROUND(AVG(CASE WHEN useful = 0 THEN 1.0 ELSE 0.0 END), 3) AS zero_fraction,
    ROUND(AVG(useful), 2) AS mean_useful
FROM review_fact_track_b
WHERE categories IS NOT NULL
GROUP BY 1
HAVING COUNT(*) >= 1000
ORDER BY zero_fraction DESC;
```

### 3.3 Stage 2: Age Confounding Analysis

**Review age computation:**

```sql
-- Preferred approach: derived view so shared curated tables stay immutable
CREATE OR REPLACE VIEW review_with_age AS
SELECT
    *,
    DATEDIFF('day', review_date, DATE :snapshot_reference_date) AS review_age_days,
    CASE
        WHEN DATEDIFF('day', review_date, DATE :snapshot_reference_date) <= 90 THEN 'A: 0-90d'
        WHEN DATEDIFF('day', review_date, DATE :snapshot_reference_date) <= 180 THEN 'B: 91-180d'
        WHEN DATEDIFF('day', review_date, DATE :snapshot_reference_date) <= 365 THEN 'C: 181-365d'
        WHEN DATEDIFF('day', review_date, DATE :snapshot_reference_date) <= 730 THEN 'D: 366-730d'
        WHEN DATEDIFF('day', review_date, DATE :snapshot_reference_date) <= 1825 THEN 'E: 731d-5y'
        ELSE 'F: 5y+'
    END AS age_bucket
FROM review_fact_track_b;
```

**Age bucket thresholds rationale:**

| Bucket | Range | Rationale |
|---|---|---|
| A: 0-90d | 0-3 months | Very new reviews; minimal exposure time; likely sparse useful votes |
| B: 91-180d | 3-6 months | Short exposure; useful counts starting to differentiate |
| C: 181-365d | 6-12 months | Moderate exposure; reasonable comparison window |
| D: 366-730d | 1-2 years | Established reviews; good signal |
| E: 731d-5y | 2-5 years | Long exposure; mature vote counts |
| F: 5y+ | 5+ years | Very old reviews; potential plateau in vote accumulation |

**Age confounding quantification:**

```sql
-- Mean useful by age bucket
SELECT
    age_bucket,
    COUNT(*) AS n,
    ROUND(AVG(useful), 3) AS mean_useful,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY useful) AS median_useful,
    ROUND(AVG(CASE WHEN useful = 0 THEN 1.0 ELSE 0.0 END), 3) AS pct_zero
FROM review_with_age
GROUP BY age_bucket
ORDER BY age_bucket;
```

**Partial correlation** (Python):

```python
import duckdb
import numpy as np
from scipy import stats

con = duckdb.connect("data/yelp.duckdb", read_only=True)
df = con.execute("""
    SELECT useful, review_age_days, text_word_count
    FROM review_with_age
    WHERE useful IS NOT NULL AND review_age_days IS NOT NULL
""").fetchdf()

# Spearman correlation: useful vs age
rho_age, p_age = stats.spearmanr(df["useful"], df["review_age_days"])

# Partial correlation: text_length vs useful, controlling for age
# Using residual method
from sklearn.linear_model import LinearRegression
age_resid_useful = df["useful"] - LinearRegression().fit(
    df[["review_age_days"]], df["useful"]
).predict(df[["review_age_days"]])
age_resid_textlen = df["text_word_count"] - LinearRegression().fit(
    df[["review_age_days"]], df["text_word_count"]
).predict(df[["review_age_days"]])
partial_rho, partial_p = stats.spearmanr(age_resid_useful, age_resid_textlen)
```

### 3.4 Stage 3: Ranking Group Construction

**Business-first grouping:**

```sql
-- Group: business_id x age_bucket
SELECT
    business_id,
    age_bucket,
    COUNT(*) AS group_size,
    COUNT(DISTINCT useful) AS distinct_useful_values,
    ROUND(AVG(CASE WHEN useful = 0 THEN 1.0 ELSE 0.0 END), 3) AS pct_zero,

    -- Tie rate: fraction of reviews sharing the same useful count as at least one other
    1.0 - (COUNT(DISTINCT useful)::DOUBLE / COUNT(*)) AS approx_tie_rate

FROM review_with_age
GROUP BY business_id, age_bucket;
```

**Qualifying group criteria:**

```sql
-- Groups with at least 5 reviews AND at least 2 distinct useful values
CREATE OR REPLACE VIEW qualifying_biz_groups AS
SELECT *
FROM (
    SELECT
        business_id AS group_id,
        'business' AS group_type,
        age_bucket,
        COUNT(*) AS group_size,
        COUNT(DISTINCT useful) AS distinct_useful
    FROM review_with_age
    GROUP BY business_id, age_bucket
) sub
WHERE group_size >= 5
  AND distinct_useful >= 2;
```

**Category fallback for small businesses:**

```sql
-- Reviews not covered by qualifying business groups
CREATE OR REPLACE VIEW uncovered_reviews AS
SELECT rwa.*
FROM review_with_age rwa
LEFT JOIN qualifying_biz_groups qbg
    ON rwa.business_id = qbg.group_id
    AND rwa.age_bucket = qbg.age_bucket
WHERE qbg.group_id IS NULL;

-- Category-level fallback groups
CREATE OR REPLACE VIEW qualifying_cat_groups AS
SELECT *
FROM (
    SELECT
        TRIM(SPLIT_PART(categories, ',', 1)) || '::' || city AS group_id,
        'category_city' AS group_type,
        age_bucket,
        COUNT(*) AS group_size,
        COUNT(DISTINCT useful) AS distinct_useful
    FROM uncovered_reviews
    WHERE categories IS NOT NULL
    GROUP BY TRIM(SPLIT_PART(categories, ',', 1)) || '::' || city, age_bucket
) sub
WHERE group_size >= 10
  AND distinct_useful >= 3;
```

**Coverage report:**

```sql
SELECT
    'business-level' AS group_type,
    COUNT(*) AS qualifying_groups,
    SUM(group_size) AS reviews_covered
FROM qualifying_biz_groups
UNION ALL
SELECT
    'category-city fallback',
    COUNT(*),
    SUM(group_size)
FROM qualifying_cat_groups;
```

### 3.5 Stage 4: Label Construction

Four candidate label schemes, all computed within ranking groups:

```sql
-- Label construction within groups
CREATE OR REPLACE TABLE label_candidates AS
WITH grouped_reviews AS (
    -- Combine business-level and category-fallback groups
    SELECT
        rwa.review_id,
        rwa.useful,
        rwa.age_bucket,
        COALESCE(qbg.group_id, qcg.group_id) AS group_id,
        COALESCE(qbg.group_type, qcg.group_type) AS group_type
    FROM review_with_age rwa
    LEFT JOIN qualifying_biz_groups qbg
        ON rwa.business_id = qbg.group_id AND rwa.age_bucket = qbg.age_bucket
    LEFT JOIN qualifying_cat_groups qcg
        ON (TRIM(SPLIT_PART(rwa.categories, ',', 1)) || '::' || rwa.city) = qcg.group_id
        AND rwa.age_bucket = qcg.age_bucket
    WHERE COALESCE(qbg.group_id, qcg.group_id) IS NOT NULL
)
SELECT
    review_id,
    group_type,
    group_id,
    age_bucket,
    useful,

    -- Label 1: Binary (useful > 0)
    CASE WHEN useful > 0 THEN 1 ELSE 0 END AS label_binary,

    -- Label 2: Graded (ordinal buckets)
    CASE
        WHEN useful = 0 THEN 0
        WHEN useful = 1 THEN 1
        WHEN useful BETWEEN 2 AND 4 THEN 2
        WHEN useful BETWEEN 5 AND 9 THEN 3
        ELSE 4
    END AS label_graded,

    -- Label 3: Within-group percentile
    PERCENT_RANK() OVER (
        PARTITION BY group_id, age_bucket
        ORDER BY useful
    ) AS label_percentile,

    -- Label 4: Top-decile within group
    CASE
        WHEN PERCENT_RANK() OVER (
            PARTITION BY group_id, age_bucket
            ORDER BY useful
        ) >= 0.90 THEN 1
        ELSE 0
    END AS label_top_decile

FROM grouped_reviews;
```

**Label scheme comparison:**

```sql
SELECT
    'binary' AS scheme,
    COUNT(*) AS total,
    ROUND(AVG(label_binary), 3) AS positive_rate,
    NULL AS mean_label
FROM label_candidates
UNION ALL
SELECT
    'graded',
    COUNT(*),
    NULL,
    ROUND(AVG(label_graded), 3)
FROM label_candidates
UNION ALL
SELECT
    'top_decile',
    COUNT(*),
    ROUND(AVG(label_top_decile), 3),
    NULL
FROM label_candidates;
```

**Recommendation criteria for primary label:**
- **Binary** is simplest but may have imbalanced classes (if zero_fraction is 65%, positive rate is 35%).
- **Graded** preserves ordinal information but may have heavy concentration in grade 0.
- **Within-group percentile** is continuous and normalized, good for pointwise regression.
- **Top-decile** creates a balanced-ish binary target (~10% positive) suitable for ranking metrics like NDCG.

**Recommended default: Within-group percentile** as the primary label, with **top-decile** as a secondary evaluation target for NDCG@K computation.

### 3.6 Stage 5: Feature Correlates Within Age Buckets

```sql
-- Age-controlled correlation: text length vs useful
SELECT
    age_bucket,
    CORR(text_word_count, useful) AS pearson_textlen_useful,
    CORR(review_stars, useful) AS pearson_stars_useful,
    COUNT(*) AS n
FROM review_with_age
GROUP BY age_bucket
ORDER BY age_bucket;
```

**Elite status effect:**

```sql
SELECT
    age_bucket,
    CASE WHEN elite IS NOT NULL AND elite != '' THEN 'elite' ELSE 'non-elite' END AS is_elite,
    COUNT(*) AS n,
    ROUND(AVG(useful), 3) AS mean_useful,
    ROUND(AVG(CASE WHEN useful > 0 THEN 1.0 ELSE 0.0 END), 3) AS has_any_useful
FROM review_with_age
GROUP BY age_bucket, is_elite
ORDER BY age_bucket, is_elite;
```

### 3.7 Stage 6: Pairwise/Listwise Feasibility

**Pairwise count estimation:**

```sql
-- For each qualifying group, count valid non-tied pairs
WITH group_value_counts AS (
    SELECT
        group_id,
        group_type,
        age_bucket,
        useful,
        COUNT(*) AS value_count
    FROM label_candidates
    GROUP BY group_id, group_type, age_bucket, useful
),
group_pair_stats AS (
    SELECT
        group_id,
        group_type,
        age_bucket,
        SUM(value_count) AS group_size,
        SUM(value_count * (value_count - 1) / 2) AS tied_pairs
    FROM group_value_counts
    GROUP BY group_id, group_type, age_bucket
)
SELECT
    group_type,
    age_bucket,
    COUNT(*) AS n_groups,
    AVG(group_size) AS avg_group_size,
    AVG(group_size * (group_size - 1) / 2 - tied_pairs) AS avg_valid_pairs,
    SUM(group_size * (group_size - 1) / 2 - tied_pairs) AS total_valid_pairs,
    SUM(group_size) AS total_reviews
FROM group_pair_stats
GROUP BY group_type, age_bucket
ORDER BY group_type, age_bucket;
```

**Listwise feasibility:**

```sql
-- Groups large enough for listwise training (at least 10 items per list)
SELECT
    group_type,
    age_bucket,
    COUNT(*) AS n_groups_ge10,
    AVG(group_size) AS avg_list_length,
    SUM(group_size) AS total_reviews
FROM (
    SELECT group_id, group_type, age_bucket, COUNT(*) AS group_size
    FROM label_candidates
    GROUP BY group_id, group_type, age_bucket
    HAVING COUNT(*) >= 10
) sub
GROUP BY group_type, age_bucket
ORDER BY group_type, age_bucket;
```

**Decision framework:**
- If business-level groups produce >50K valid pairs across age buckets: **pairwise LTR is feasible**.
- If business-level groups have an average list length >= 10 for at least 5K groups: **listwise LTR is feasible**.
- If neither threshold is met at business level, rely on **category-city fallback groups** for training and evaluate on the business groups that do qualify.

### 3.8 Stage 7: Leakage and Scope Check

```python
# src/eda/track_b/leakage_scope_check.py
import duckdb
from dataclasses import dataclass

@dataclass(frozen=True)
class ScopeCheckResult:
    check_name: str
    severity: str
    status: str
    flagged_count: int
    detail: str

def run_track_b_scope_checks(db_path: str) -> list[ScopeCheckResult]:
    con = duckdb.connect(db_path, read_only=True)
    results: list[ScopeCheckResult] = []

    # Check 1: funny/cool do not appear in curated Track B tables
    banned_cols = con.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_name IN ('review_fact_track_b', 'review_with_age', 'label_candidates')
          AND column_name IN ('funny', 'cool')
        ORDER BY table_name, column_name
    """).fetchall()
    results.append(ScopeCheckResult(
        check_name="funny_cool_excluded",
        severity="CRITICAL",
        status="FAIL" if banned_cols else "PASS",
        flagged_count=len(banned_cols),
        detail=(
            "Track B curated tables must not expose funny/cool as candidate features. "
            f"Found banned columns: {banned_cols}"
        ),
    ))

    # Check 2: All label rows must carry age_bucket
    missing_age_bucket = con.execute("""
        SELECT COUNT(*)
        FROM label_candidates
        WHERE age_bucket IS NULL
    """).fetchone()[0]
    results.append(ScopeCheckResult(
        check_name="label_age_bucket_present",
        severity="CRITICAL",
        status="FAIL" if missing_age_bucket > 0 else "PASS",
        flagged_count=missing_age_bucket,
        detail=(
            f"{missing_age_bucket} label rows are missing age_bucket. "
            "All Track B labels must be age-controlled."
        ),
    ))

    # Check 3: Percentile labels must match a recomputation partitioned by group_id and age_bucket
    label_partition_mismatch = con.execute("""
        WITH expected AS (
            SELECT
                review_id,
                PERCENT_RANK() OVER (
                    PARTITION BY group_id, age_bucket
                    ORDER BY useful
                ) AS expected_percentile
            FROM label_candidates
        )
        SELECT COUNT(*)
        FROM label_candidates lc
        JOIN expected e USING (review_id)
        WHERE ABS(lc.label_percentile - e.expected_percentile) > 1e-12
    """).fetchone()[0]
    results.append(ScopeCheckResult(
        check_name="age_control_applied",
        severity="CRITICAL",
        status="FAIL" if label_partition_mismatch > 0 else "PASS",
        flagged_count=label_partition_mismatch,
        detail=(
            f"{label_partition_mismatch} label rows disagree with an age-partitioned "
            "percentile recomputation. Should be 0."
        ),
    ))

    # Check 4: Curated Track B tables should not carry raw review text
    raw_text_cols = con.execute("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_name IN ('review_fact_track_b', 'review_with_age', 'label_candidates')
          AND column_name IN ('text', 'review_text')
        ORDER BY table_name, column_name
    """).fetchall()
    results.append(ScopeCheckResult(
        check_name="aggregate_only_outputs",
        severity="CRITICAL",
        status="FAIL" if raw_text_cols else "PASS",
        flagged_count=len(raw_text_cols),
        detail=(
            "Curated Track B tables should not expose raw review text. "
            f"Found text-bearing columns: {raw_text_cols}"
        ),
    ))

    con.close()
    return results
```

**Required minimum checks beyond the representative code above:**
- verify labels never compare reviews across different age buckets; any occurrence is a Stage 7 failure
- scan all `outputs/tables/track_b_*` and `outputs/logs/track_b_*` files with `re.search(..., re.IGNORECASE)` for unsupported temporal claims
- record named findings in the Stage 7 log and fail on any match

Minimum prohibited temporal-claim patterns:

```text
predict\s+future
vote\s+growth
future\s+useful(ness)?
temporal\s+target
vote.*(trajectory|trend|accumulate)
usefulness.at.time
reconstruct.*(vote|useful)
```

**Representative verification query (for Check 3):**

```sql
WITH expected AS (
    SELECT
        review_id,
        PERCENT_RANK() OVER (
            PARTITION BY group_id, age_bucket
            ORDER BY useful
        ) AS expected_percentile
    FROM label_candidates
)
SELECT COUNT(*) AS mismatched_rows
FROM label_candidates lc
JOIN expected e USING (review_id)
WHERE ABS(lc.label_percentile - e.expected_percentile) > 1e-12;
-- Pass criterion: mismatched_rows = 0
```

### 3.9 Track B Stage Dependency Graph

```
Stage 0 (shared): ingest + validate + build_review_fact
    |
    v
Stage 1: usefulness_distribution  (independent)
    |
    v
Stage 2: age_confounding  (builds review_with_age view; needed by all subsequent)
    |
    +----> Stage 3: ranking_group_analysis  (depends on Stage 2)
    |          |
    |          v
    |      Stage 4: label_construction  (depends on Stage 3)
    |          |
    |          v
    +----> Stage 5: feature_correlates  (depends on Stage 2)
    |      Stage 6: training_feasibility  (depends on Stages 3, 4)
    |
    +----> Stage 7: leakage_scope_check  (depends on Stage 4)
               |
               v
           Stage 8: summary_report  (depends on all prior)
```

**Parallelism opportunity**: After Stage 2 (which must run first to establish age buckets), Stages 3 and 5 can run in parallel. Stage 4 depends on Stage 3. Stage 6 depends on Stages 3 and 4. Stages 5 and 7 can run in parallel with the Stage 3->4->6 chain.

---

## Part 4: Shared Infrastructure

### 4.1 Config Schema

#### configs/base.yaml

```yaml
# Shared configuration for all tracks
project:
  name: "yelp-semester-project"
  version: "1.0"

paths:
  raw_dir: "data/raw"
  interim_dir: "data/interim"
  curated_dir: "data/curated"
  outputs_dir: "outputs"
  figures_dir: "outputs/figures"
  tables_dir: "outputs/tables"
  logs_dir: "outputs/logs"
  db_path: "data/yelp.duckdb"

ingestion:
  tar_path: "Dataset(Raw)/Yelp-JSON/Yelp JSON/yelp_dataset.tar"
  memory_limit_gb: 4
  threads: 4
  parquet_compression: "zstd"

entities:
  - name: "business"
    source_file: "yelp_academic_dataset_business.json"
    primary_key: "business_id"
  - name: "review"
    source_file: "yelp_academic_dataset_review.json"
    primary_key: "review_id"
  - name: "user"
    source_file: "yelp_academic_dataset_user.json"
    primary_key: "user_id"
  - name: "tip"
    source_file: "yelp_academic_dataset_tip.json"
    primary_key: null  # composite key
  - name: "checkin"
    source_file: "yelp_academic_dataset_checkin.json"
    primary_key: "business_id"

quality:
  review_fact_max_row_loss_fraction: 0.001

random_seed: 42
log_level: "INFO"
```

#### configs/track_a.yaml

```yaml
# Track A: Future Star Rating Prediction
extends: "configs/base.yaml"

track:
  name: "track_a"
  label: "Future Star Rating Prediction"

splits:
  # Placeholders -- finalized during Stage 5
  t1: "2019-06-01"
  t2: "2020-09-01"
  # Candidate percentiles to evaluate
  candidates:
    - { t1_pct: 65, t2_pct: 82 }
    - { t1_pct: 70, t2_pct: 85 }
    - { t1_pct: 70, t2_pct: 90 }
    - { t1_pct: 75, t2_pct: 88 }

eda:
  sentiment_sample_size: 50000
  sentiment_random_seed: 42
  cold_start_threshold: 5  # users/businesses with <= N prior reviews

leakage:
  # Fields that MUST NOT be used as Track A features
  banned_features:
    - "business.stars"
    - "business.review_count"
    - "business.is_open"
    - "user.average_stars"
    - "user.review_count"
    - "user.fans"
    - "user.elite"

quality:
  ks_threshold: 0.05  # max KS stat for split validation
  min_split_fraction: 0.10  # each split must have >= 10% of reviews
  text_nonnull_threshold: 0.99
```

#### configs/track_b.yaml

```yaml
# Track B: Usefulness Ranking
extends: "configs/base.yaml"

track:
  name: "track_b"
  label: "Snapshot Usefulness Ranking"

snapshot_metadata:
  path: "data/curated/snapshot_metadata.json"
  required_fields:
    - "snapshot_reference_date"
    - "dataset_release_tag"

age_buckets:
  thresholds_days: [90, 180, 365, 730, 1825]
  labels: ["A: 0-90d", "B: 91-180d", "C: 181-365d", "D: 366-730d", "E: 731d-5y", "F: 5y+"]

ranking_groups:
  # Business-level groups (primary)
  business:
    min_group_size: 5
    min_distinct_useful: 2
  # Category-city fallback groups
  category_city:
    min_group_size: 10
    min_distinct_useful: 3

labels:
  primary: "within_group_percentile"
  secondary: "top_decile"
  graded_bins: [0, 1, 2, 4, 9]  # boundaries for graded label

leakage:
  # Fields that MUST NOT be used as features
  banned_features:
    - "review.funny"
    - "review.cool"

quality:
  useful_nonnull_threshold: 0.999
  min_qualifying_groups: 1000
  max_single_class_fraction: 0.90
```

### 4.2 Shared Ingestion and Curation Modules

#### Module: src/ingest/load_yelp_json.py

```python
"""
CLI entry point: python -m src.ingest.load_yelp_json --config configs/base.yaml

Responsibilities:
1. Extract tar archive to data/raw/ (if not already extracted)
2. Validate JSON structure (first 100 lines per entity)
3. Load all entities into DuckDB with typed schemas
4. Log row counts and timing
"""
import argparse
import logging
import tarfile
import time
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Yelp JSON to DuckDB")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    raw_dir = Path(config["paths"]["raw_dir"])
    db_path = Path(config["paths"]["db_path"])

    # Step 1: Extract tar if needed
    if not any(raw_dir.glob("*.json")):
        logger.info("Extracting tar archive...")
        _extract_tar(config["ingestion"]["tar_path"], raw_dir)

    # Step 2: Validate JSON structure
    logger.info("Validating JSON structure...")
    _validate_all_entities(raw_dir, config["entities"])

    # Step 3: Load to DuckDB
    logger.info("Loading to DuckDB at %s", db_path)
    t0 = time.time()
    _load_to_duckdb(raw_dir, db_path, config["ingestion"])
    logger.info("DuckDB load complete in %.1f seconds", time.time() - t0)

    # Step 4: Log row counts
    _log_row_counts(db_path)


def _extract_tar(tar_path: str, raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".json"):
                member.name = Path(member.name).name  # strip directory prefix
                tar.extract(member, raw_dir)


if __name__ == "__main__":
    main()
```

#### Module: src/curate/build_review_fact.py

```python
"""
CLI entry point: python -m src.curate.build_review_fact --config configs/base.yaml

Builds the Track A-safe review_fact table, the Track B snapshot view,
and exports both curated artifacts to Parquet.
"""
import argparse
import logging
from pathlib import Path

import duckdb
import yaml

logger = logging.getLogger(__name__)

REVIEW_FACT_SQL = """
CREATE OR REPLACE TABLE review_fact AS
SELECT
    r.review_id,
    r.user_id,
    r.business_id,
    r.stars         AS review_stars,
    r.review_date,
    r.useful,
    LENGTH(r.text)  AS text_char_count,
    ARRAY_LENGTH(STRING_SPLIT(TRIM(r.text), ' ')) AS text_word_count,
    b.city,
    b.state,
    b.categories,
    b.latitude,
    b.longitude,
    u.yelping_since,
    EXTRACT(YEAR FROM r.review_date)  AS review_year,
    EXTRACT(MONTH FROM r.review_date) AS review_month,
    DATEDIFF('day', u.yelping_since, r.review_date) AS user_tenure_days
FROM review r
JOIN business b ON r.business_id = b.business_id
JOIN "user" u ON r.user_id = u.user_id
WHERE r.review_date IS NOT NULL
  AND r.stars IS NOT NULL
"""

REVIEW_FACT_TRACK_B_SQL = """
CREATE OR REPLACE VIEW review_fact_track_b AS
SELECT
    rf.*,
    b.is_open,
    u.fans,
    u.elite
FROM review_fact rf
JOIN business b ON rf.business_id = b.business_id
JOIN "user" u ON rf.user_id = u.user_id
"""

def main() -> None:
    parser = argparse.ArgumentParser(description="Build review_fact table")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    db_path = config["paths"]["db_path"]
    curated_dir = Path(config["paths"]["curated_dir"])
    curated_dir.mkdir(parents=True, exist_ok=True)
    max_drop_fraction = config["quality"]["review_fact_max_row_loss_fraction"]

    con = duckdb.connect(db_path)
    logger.info("Building review_fact table...")
    con.execute(REVIEW_FACT_SQL)
    con.execute(REVIEW_FACT_TRACK_B_SQL)

    # Validation
    raw_count = con.execute("SELECT COUNT(*) FROM review").fetchone()[0]
    fact_count = con.execute("SELECT COUNT(*) FROM review_fact").fetchone()[0]
    dropped = raw_count - fact_count
    drop_fraction = dropped / raw_count if raw_count else 0.0

    logger.info(
        "review: %d rows, review_fact: %d rows, dropped: %d (%.4f%%)",
        raw_count, fact_count, dropped, drop_fraction * 100
    )
    if drop_fraction > max_drop_fraction:
        raise ValueError(
            "review_fact row loss exceeds threshold: "
            f"{drop_fraction:.4%} > {max_drop_fraction:.4%}"
        )
    if dropped > 0:
        logger.warning(
            "%d reviews dropped during join; log orphan review_id values and missing foreign-key reasons before continuing",
            dropped,
        )

    # Export to Parquet
    track_a_out = curated_dir / "review_fact.parquet"
    track_b_out = curated_dir / "review_fact_track_b.parquet"
    con.execute(f"COPY review_fact TO '{track_a_out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.execute(f"COPY review_fact_track_b TO '{track_b_out}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    logger.info("Exported review_fact to %s", track_a_out)
    logger.info("Exported review_fact_track_b to %s", track_b_out)
    # Also write data/curated/snapshot_metadata.json with snapshot_reference_date,
    # dataset_release_tag, and optional computed_from provenance.

    con.close()


if __name__ == "__main__":
    main()
```

### 4.3 Logging and Validation Framework

```python
# src/common/logging_config.py
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
    track: str,
    stage: str,
    log_dir: str = "outputs/logs",
    log_level: str = "INFO",
) -> logging.Logger:
    """Configure logging to both console and a timestamped log file."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"{track}_{stage}_{timestamp}.log"

    logger = logging.getLogger(f"{track}.{stage}")
    logger.setLevel(getattr(logging, log_level.upper()))

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    ))

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(getattr(logging, log_level.upper()))
    ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
```

```python
# src/common/config.py
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str) -> dict[str, Any]:
    """Load a track config, merging with base config if 'extends' is specified."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    if "extends" in config:
        base_path = config.pop("extends")
        with open(base_path) as f:
            base_config = yaml.safe_load(f)
        # Shallow merge: track config overrides base
        merged = {**base_config, **config}
        # Deep merge for nested keys
        for key in ["paths", "ingestion", "quality"]:
            if key in base_config and key in config:
                merged[key] = {**base_config[key], **config[key]}
        return merged

    return config
```

### 4.4 CLI Entry Point Pattern

Every stage follows the same structure:

```python
# src/eda/track_X/stage_name.py
"""
CLI: python -m src.eda.track_X.stage_name --config configs/track_X.yaml
"""
import argparse
from pathlib import Path

import duckdb

from src.common.config import load_config
from src.common.logging_config import setup_logging


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    logger = setup_logging(
        track=config["track"]["name"],
        stage="stage_name",
        log_dir=config["paths"]["logs_dir"],
        log_level=config.get("log_level", "INFO"),
    )

    db_path = config["paths"]["db_path"]
    tables_dir = Path(config["paths"]["tables_dir"])
    figures_dir = Path(config["paths"]["figures_dir"])
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(db_path, read_only=True)

    try:
        logger.info("Starting stage_name...")
        # --- Stage logic here ---
        logger.info("stage_name complete.")
    except Exception as e:
        logger.error("stage_name failed: %s", e)
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
```

### 4.5 Full Execution Sequence

```bash
# ============================================================
# Phase 0: Ingestion and curation (shared across all tracks)
# ============================================================
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml

# ============================================================
# Phase 1: Track A EDA (Stages 1-4 can run in parallel)
# ============================================================
# Parallel batch:
python -m src.eda.track_a.temporal_profile --config configs/track_a.yaml &
python -m src.eda.track_a.text_profile --config configs/track_a.yaml &
python -m src.eda.track_a.user_history_profile --config configs/track_a.yaml &
python -m src.eda.track_a.business_attr_profile --config configs/track_a.yaml &
wait

# Sequential chain:
python -m src.eda.track_a.split_selection --config configs/track_a.yaml
python -m src.eda.track_a.leakage_audit --config configs/track_a.yaml
python -m src.eda.track_a.feature_availability --config configs/track_a.yaml
python -m src.eda.track_a.summary_report --config configs/track_a.yaml

# ============================================================
# Phase 2: Track B EDA
# ============================================================
python -m src.eda.track_b.usefulness_distribution --config configs/track_b.yaml
python -m src.eda.track_b.age_confounding --config configs/track_b.yaml

# After Stage 2, parallel batch:
python -m src.eda.track_b.ranking_group_analysis --config configs/track_b.yaml &
python -m src.eda.track_b.feature_correlates --config configs/track_b.yaml &
wait

python -m src.eda.track_b.label_construction --config configs/track_b.yaml
python -m src.eda.track_b.training_feasibility --config configs/track_b.yaml

# Parallel:
python -m src.eda.track_b.leakage_scope_check --config configs/track_b.yaml

python -m src.eda.track_b.summary_report --config configs/track_b.yaml
```

### 4.6 Dependencies (requirements.txt)

```
duckdb>=1.1.0
polars>=1.0.0
pandas>=2.2.0
pyarrow>=17.0.0
matplotlib>=3.9.0
seaborn>=0.13.0
scipy>=1.14.0
scikit-learn>=1.5.0
textblob>=0.18.0
pyyaml>=6.0.0
```

### 4.7 Output Artifact Summary

#### Track A Expected Outputs

| Stage | File | Format |
|---|---|---|
| S1 | `track_a_s1_stars_by_year_month.parquet` | Parquet |
| S1 | `track_a_s1_review_volume_by_period.parquet` | Parquet |
| S1 | `track_a_s1_star_distribution_over_time.png` | PNG |
| S1 | `track_a_s1_review_volume_timeline.png` | PNG |
| S2 | `track_a_s2_text_length_stats.parquet` | Parquet |
| S2 | `track_a_s2_text_length_by_star.png` | PNG |
| S2 | `track_a_s2_text_length_distribution.png` | PNG |
| S3 | `track_a_s3_user_history_depth.parquet` | Parquet |
| S3 | `track_a_s3_user_prior_review_count_dist.png` | PNG |
| S3 | `track_a_s3_user_tenure_vs_rating_var.png` | PNG |
| S4 | `track_a_s4_attr_completeness_by_category.parquet` | Parquet |
| S4 | `track_a_s4_attr_completeness_by_city.parquet` | Parquet |
| S4 | `track_a_s4_attr_null_rate_heatmap.png` | PNG |
| S5 | `track_a_s5_candidate_splits.parquet` | Parquet |
| S5 | `track_a_s5_split_star_balance.parquet` | Parquet |
| S5 | `track_a_s5_split_comparison.png` | PNG |
| S6 | `track_a_s6_leakage_report.parquet` | Parquet |
| S6 | `track_a_s6_leakage_audit.log` | Log |
| S7 | `track_a_s7_feature_availability.parquet` | Parquet |
| S7 | `track_a_s7_feature_coverage_bars.png` | PNG |
| S8 | `track_a_s8_eda_summary.md` | Markdown |

#### Track B Expected Outputs

| Stage | File | Format |
|---|---|---|
| S1 | `track_b_s1_useful_vote_distribution.parquet` | Parquet |
| S1 | `track_b_s1_age_distribution.parquet` | Parquet |
| S1 | `track_b_s1_useful_histogram.png` | PNG |
| S1 | `track_b_s1_zero_fraction_by_category.png` | PNG |
| S2 | `track_b_s2_age_effect_summary.parquet` | Parquet |
| S2 | `track_b_s2_useful_by_age_bucket.png` | PNG |
| S2 | `track_b_s2_textlen_vs_useful_within_age.png` | PNG |
| S3 | `track_b_s3_group_sizes_by_business_age.parquet` | Parquet |
| S3 | `track_b_s3_group_sizes_by_category_age.parquet` | Parquet |
| S3 | `track_b_s3_group_size_distribution.png` | PNG |
| S4 | `track_b_s4_label_candidates.parquet` | Parquet |
| S4 | `track_b_s4_label_scheme_summary.parquet` | Parquet |
| S5 | `track_b_s5_feature_correlates.parquet` | Parquet |
| S5 | `track_b_s5_stars_vs_useful_within_age.png` | PNG |
| S5 | `track_b_s5_elite_vs_useful_within_age.png` | PNG |
| S6 | `track_b_s6_pairwise_stats.parquet` | Parquet |
| S6 | `track_b_s6_listwise_stats.parquet` | Parquet |
| S7 | `track_b_s7_leakage_scope_report.parquet` | Parquet |
| S7 | `track_b_s7_leakage_scope_check.log` | Log |
| S8 | `track_b_s8_eda_summary.md` | Markdown |

---

*End of Implementation Plan.*
