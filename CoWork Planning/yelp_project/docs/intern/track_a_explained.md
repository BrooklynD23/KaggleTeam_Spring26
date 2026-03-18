# Track A Explained: Predicting Future Star Ratings
### A Guide for New Interns

Welcome! This doc explains everything you need to know about **Track A** of our Yelp data science project — written for someone who knows a bit of Python but is new to data science. No jargon without explanation, promise.

---

## 1. What Is Track A? (The Big Picture)

**The question we're trying to answer:**
> "Can we predict what star rating a Yelp reviewer will give — before they write the review?"

Imagine you're Yelp, and you want to know: given what we know about a user's history and the business they're visiting, can we guess whether they'll leave a 1-star or a 5-star review?

That's Track A. We're not building the prediction model yet — that comes later. Right now, we're doing **EDA** (Exploratory Data Analysis), which means: *digging through the data to understand what we have, whether it's good enough to make predictions, and where potential problems are.*

---

## 2. The Data We're Working With

Yelp released a large dataset for research. It has 5 types of records:

| Entity | What it is | Key fields |
|--------|-----------|------------|
| **review** | A single review someone wrote | star rating, review text, date, useful/funny/cool votes |
| **business** | A restaurant, shop, etc. | name, city, categories, overall star rating |
| **user** | The person who wrote reviews | when they joined Yelp, how many reviews they've written |
| **tip** | Short tip (like a tweet) left at a business | text, date |
| **checkin** | Record that someone checked in at a business | business, dates |

For Track A, our main working file is **`data/curated/review_fact.parquet`** — a pre-joined table that combines the key columns from review, business, and user into one convenient file. Think of it like a spreadsheet where each row = one review, and the columns include info about the business and the reviewer.

### What is Parquet?
A Parquet file is like a supercharged CSV. It stores data in a compressed, column-organized format that's much faster to read than a regular CSV, especially for large datasets. You can read it with `pandas` or `polars` in Python.

---

## 3. The 8-Stage Pipeline

Our analysis runs in 8 stages, like steps in a recipe. Each stage produces output files (charts and data tables) that feed into the next stage.

### Stage 1: Temporal Profile
**What it does:** Looks at how many reviews were written each month, and how star ratings are distributed over time.

**Why it matters:** We need to understand the data's timeline before we can make predictions. Are there more reviews in certain years? Did average ratings shift over time?

**Output:** Charts like "how many reviews per month" and "star rating breakdown by year."

**Analogy:** Like checking if a dataset from a store has sales records going back to 1990 or just the last 6 months — it matters for how we split training/test data.

---

### Stage 2: Text Profile
**What it does:** Analyzes the review text — but only in aggregate (we never show raw text). Measures things like: average review length in words, and sentiment (how positive/negative the text sounds, using a quick scoring tool).

**Why it matters:** Review text is a potential feature for prediction. We need to know if reviews are long/short, positive/negative on average.

---

### Stage 3: User History Profile
**What it does:** For each review, looks at how many reviews that user had written *before* this one.

**Why it matters:** A user's past behavior is a strong signal for prediction. But we can only use their *history up to that point* — not their future activity. This stage checks how deep each user's history is.

**Key concept:** "As-of history" — only what the user had done *before* this review date.

---

### Stage 4: Business Attribute Profile
**What it does:** Checks how complete the business info is. Yelp businesses have attributes like "Accepts Credit Cards", "Outdoor Seating", etc. But many businesses leave these blank.

**Why it matters:** If 80% of businesses have empty attributes, we can't use attributes as a reliable feature for prediction.

---

### Stage 5: Split Selection
**What it does:** Chooses two cutoff dates — **T₁** and **T₂** — that divide our data into train / validation / test sets.

**Why it matters:** We need to train on *old* reviews and test on *newer* reviews, to simulate real-world prediction. This stage finds the best dates to make that split while keeping enough data in each portion.

**Analogy:** If you're studying for a history exam, you study events from 1900-2000, and the exam tests you on events from 2000-2010. That's a time split. We do the same here — train on old reviews, test on new ones.

The config has candidate splits to try:
```yaml
splits:
  t1: "2019-06-01"
  t2: "2020-09-01"
```

---

### Stage 6: Leakage Audit
**What it does:** Checks that none of our features "cheat" by accidentally using future data.

**Why it matters:** This is the most important quality check. See Section 4 below for a full explanation of leakage.

---

### Stage 7: Feature Availability Matrix
**What it does:** Creates a report showing which features are available for which reviews, and how complete/reliable each feature is.

**Why it matters:** Before building a model, we need to know which features we can actually use. If a feature is missing for 40% of rows, that's a problem.

---

### Stage 8: Summary Report
**What it does:** Writes a final Markdown report summarizing everything learned in Stages 1-7.

**Why it matters:** This is the "handoff" — the summary tells the modeling team what data they have to work with and what to watch out for.

---

## 4. Key Rules to Know

### What is Temporal Leakage? (The #1 Rule)

**Leakage** = accidentally using future information to predict the past.

**Analogy:** Imagine you're predicting whether a stock will go up tomorrow. If you accidentally look at tomorrow's price to build your features, your model will look amazing in testing — but it will fail completely in real use because tomorrow's price isn't available today.

In our case: if we use a user's *final, total* review count (which includes reviews they wrote *after* the review we're predicting), we're cheating — that info wasn't available at prediction time.

### The Banned Fields
These fields are **not allowed** in Track A features because they reflect the *current state* of the data (the "snapshot"), not what was true at the time of the review:

| Banned Field | Why It's Banned |
|-------------|----------------|
| `business.stars` | This is the business's current average — includes reviews written after our review |
| `business.review_count` | Current total — includes future reviews |
| `business.is_open` | Current status — business could have opened/closed |
| `user.average_stars` | User's lifetime average — includes future reviews |
| `user.review_count` | Total count — includes future reviews |
| `user.fans` | Current fan count — accumulates over time |
| `user.elite` | Current elite status — can change over time |

### What is an "As-Of" Feature?
An as-of feature is computed using *only data that existed at or before the review date*.

For example:
- **NOT OK:** `user.review_count` (their all-time total)
- **OK:** count of reviews that user wrote *strictly before this review's date*

---

## 5. The Code Structure

Here's a map of the Python files you might work with:

### `src/ingest/load_yelp_json.py`
**What it does:** Reads the raw Yelp JSON files and loads them into a DuckDB database.

**Key function:** `run(config)` — the main entry point that extracts the tar archive and loads all 5 entity tables (business, review, user, tip, checkin).

**DuckDB?** DuckDB is a fast, in-process SQL database — think SQLite but way faster for analytics. It stores everything in a single `.duckdb` file.

---

### `src/validate/schema_checks.py`
**What it does:** After loading the data, this checks data quality. Are there too many null values? Do dates look reasonable?

**Key function:** `run(config)` — runs checks on all entities and returns a report (PASS/FAIL).

**Key concept:** The `NULL_THRESHOLD = 0.01` means: if more than 1% of a key column is missing, the check fails.

---

### `src/curate/build_review_fact.py`
**What it does:** Joins review + business + user into one "fact table" — the main working table for analysis.

**Key function:** `run(config)` — builds `review_fact`, validates row loss, exports to Parquet.

**Key concept:** "Row loss" — when we join tables, some reviews might not match a user or business (orphan rows). We allow at most 0.1% row loss before raising an error.

---

### `src/eda/track_a/temporal_profile.py`
**What it does:** Stage 1 of the EDA — analyzes star distributions and review volume over time.

**Key functions:**
- `run_star_distribution(con, curated, tables)` — counts reviews by year/month/star rating
- `run_monthly_volume(con, curated, tables)` — monthly review counts with mean/std
- `plot_star_distribution(df, figures)` — stacked bar chart of star % by year
- `plot_volume_timeline(df, figures)` — dual-axis chart of volume + mean stars

**How it works:** Uses DuckDB SQL to query the Parquet file directly (no need to load into memory first!), then uses pandas + matplotlib to create charts.

---

### `src/common/config.py`
**What it does:** Loads YAML config files. All scripts use this to read their settings.

---

## 6. Config Files

Config files control the pipeline without changing code.

### `configs/base.yaml` — Shared settings for all tracks
```yaml
paths:
  raw_dir: "data/raw"          # Where raw JSON files go
  curated_dir: "data/curated"  # Where processed Parquet files go
  db_path: "data/yelp.duckdb"  # DuckDB database file

ingestion:
  memory_limit_gb: 4    # How much RAM DuckDB can use
  threads: 4            # Parallel threads
```

### `configs/track_a.yaml` — Track A specific settings
```yaml
splits:
  t1: "2019-06-01"   # Training / validation cutoff date
  t2: "2020-09-01"   # Validation / test cutoff date

eda:
  sentiment_sample_size: 50000  # Sample 50k reviews for sentiment analysis
  cold_start_threshold: 5       # "New user" = fewer than 5 prior reviews

leakage:
  banned_features:  # These must NEVER appear in Track A models
    - "business.stars"
    - "user.average_stars"
    # ... (see file for full list)
```

**To change a setting:** Edit the YAML file and re-run the stage. No code changes needed.

---

## 7. How to Run the Pipeline

All stages follow this pattern:
```bash
python -m src.<module>.<script> --config configs/<config>.yaml
```

### Step-by-step:

```bash
# 1. Load raw JSON into DuckDB (shared step)
python -m src.ingest.load_yelp_json --config configs/base.yaml

# 2. Validate the loaded data (shared step)
python -m src.validate.schema_checks --config configs/base.yaml

# 3. Build the curated fact table (shared step)
python -m src.curate.build_review_fact --config configs/base.yaml

# 4. Run Track A Stage 1: Temporal Profile
python -m src.eda.track_a.temporal_profile --config configs/track_a.yaml
```

Or use the canonical launcher or OS wrappers:
```bash
python scripts/run_pipeline.py --approach shared
python scripts/run_pipeline.py --approach track_a
# WSL/Linux: ./run_pipeline.sh shared
# Windows:   .\run_pipeline.ps1 track_a
```

---

## 8. Glossary

| Term | Plain English |
|------|--------------|
| **EDA** | Exploratory Data Analysis — looking at your data before building a model, like reading a book before writing a report on it |
| **Parquet** | A compressed file format for tables, much faster than CSV for large data |
| **DuckDB** | A fast in-memory SQL database stored in a single file — like SQLite but built for analytics |
| **Temporal split** | Dividing data by date: train on old data, test on new data |
| **Leakage** | Accidentally using future information to build features — "cheating" that makes models look good in testing but fail in real use |
| **As-of feature** | A feature computed using only data available up to a given date — no peeking at the future |
| **Snapshot field** | A field that reflects the *current* state, not the state at a past point in time |
| **Feature** | An input variable used by a model to make a prediction (e.g., "how long is the review text?") |
| **Polars / Pandas** | Python libraries for working with tables of data |
| **CLI** | Command-Line Interface — running a program from the terminal with `python -m ...` |
| **YAML** | A simple config file format — key: value pairs |
| **Aggregate** | A summary statistic (count, mean, etc.) rather than raw individual records |

---

## 9. Quick Start Checklist for Interns

- [ ] Read `CoWork Planning/yelp_project/track_a/CLAUDE.md` for the quick reference
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Make sure the Yelp tar file is in `CoWork Planning/Dataset(Raw)/Yelp-JSON/`
- [ ] Run the shared pipeline: `python scripts/run_pipeline.py --approach shared` or `./run_pipeline.sh shared`
- [ ] Run Stage 1: `python -m src.eda.track_a.temporal_profile --config configs/track_a.yaml`
- [ ] Check outputs in `outputs/figures/` and `outputs/tables/`
- [ ] Never use the banned fields (see Section 4)
- [ ] If something breaks, check `outputs/logs/` for error details

---

*Questions? Talk to your team lead. Good luck!*
