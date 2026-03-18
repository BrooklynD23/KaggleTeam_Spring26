# Track B Explained: Ranking Which Reviews Are Most Useful
### A Guide for New Interns

Welcome! This doc explains **Track B** of our Yelp data science project in plain English — written for someone new to data science. No jargon without explanation.

---

## 1. What Is Track B? (The Big Picture)

**The question we're trying to answer:**
> "Can we figure out which reviews are most helpful to readers — and build a model that ranks them?"

When you open a Yelp page for a restaurant, you see dozens of reviews. Which ones should be shown first? Yelp has a "useful" vote system — other users can tap "Useful" on a review they found helpful. Reviews with more useful votes are presumably more valuable.

Track B asks: **can we predict/rank which reviews are most useful, using the text and metadata of the reviews themselves?**

Right now, we're not building the ranking model yet. We're doing **EDA** (Exploratory Data Analysis) — exploring and understanding the data to check if it's ready for ranking. Think of it as "doing the prep work" before cooking.

---

## 2. The Data We're Working With

Same Yelp dataset as Track A, but Track B uses a slightly different version of the main table:

**`data/curated/review_fact_track_b.parquet`** — this is the Track B version of the fact table. It includes a few extra columns that Track A can't use (like `is_open`, `fans`, `elite`) because those are safe for a snapshot-based task.

Also:
**`data/curated/snapshot_metadata.json`** — a small JSON file telling us the "snapshot date" (more on this below).

### The Yelp Entities

| Entity | What it is |
|--------|-----------|
| **review** | A single review — includes `useful`, `funny`, `cool` vote counts |
| **business** | A place — name, city, categories |
| **user** | The reviewer — join date, fan count, elite status |
| **tip** | Short tips left at a business |
| **checkin** | Records of check-ins at a business |

---

## 3. Key Concepts Before the Pipeline

Before walking through the stages, here are three key ideas you need to understand:

### What is a "Snapshot"?
The Yelp dataset was downloaded at a specific point in time — like a photograph of the database on a certain day. That date is called the **snapshot date** (stored in `snapshot_metadata.json`).

Track B is a **single-snapshot** task. This means:
- We look at the data as it existed on one specific date
- We do NOT try to track how votes changed over time
- The snapshot reference date for this project is **2022-01-19**

**Analogy:** Imagine taking a photo of a scoreboard at halftime. You know the score at that moment. Track B works with that one photo — not a video of the whole game.

### What is Exposure-Time Bias?
This is the #1 problem in Track B.

**The issue:** A review written in 2013 has had 9 years for people to read it and vote "Useful." A review written in 2021 has only had 1 year. Of course the 2013 review has more useful votes — it's not necessarily better, it's just *older*.

This is called **exposure-time bias** — older things have had more exposure to collect votes.

**Analogy:** A Wikipedia article from 2005 has had 20 years of edits and views. A new article from 2024 looks less popular, but that doesn't mean it's worse — it just hasn't had time yet.

**How we fix it:** We group reviews into **age buckets** (e.g., reviews 0-90 days old, 91-180 days old, etc.) and only compare reviews *within the same age bucket*. This way, we're only comparing reviews that had similar amounts of time to collect votes.

### What is Learning-to-Rank?
Traditional machine learning predicts a single value (like a star rating). **Learning-to-rank** instead tries to sort items — given a list of reviews, rank them from most to least useful.

There are different ways to do this:
- **Pointwise**: predict a score for each review independently
- **Pairwise**: ask "is review A more useful than review B?" for pairs
- **Listwise**: rank a whole list at once

Track B will explore whether our data supports pairwise or listwise ranking.

---

## 4. The 8-Stage Pipeline

### Stage 1: Usefulness Vote Distribution Profiling
**What it does:** Counts how many reviews have 0 useful votes vs. 1 vs. 2 vs. many.

**Why it matters:** We expect most reviews to have 0 useful votes (this is normal — most reviews never get voted on). We need to understand this distribution to design our labels.

**Typical finding:** The distribution is "zero-inflated" — like 80%+ of reviews have 0 useful votes, with a long tail.

---

### Stage 2: Review-Age Confounding Analysis
**What it does:** Shows how useful vote counts vary by review age — confirming the exposure-time bias problem.

**Why it matters:** Quantifies how much older reviews dominate in useful vote counts, justifying the need for age-controlled groups.

---

### Stage 3: Ranking Group Definition and Sizing
**What it does:** Defines the groups within which we'll rank reviews, and counts how many reviews are in each group.

**Groups are defined as:**
1. **Primary:** All reviews for a specific business (e.g., "all reviews of Joe's Pizza")
2. **Fallback:** If a business has too few reviews, group by (category + city) — e.g., "all Italian restaurant reviews in Las Vegas"

Both levels are further divided by **age bucket** — we only rank reviews against others of similar age.

**Why we need minimum group sizes:** You can't meaningfully rank 2 reviews. We require at least 5 reviews per business group and 10 per category-city group.

---

### Stage 4: Snapshot-Safe Label Construction
**What it does:** Creates the training labels — the "answer key" for what "useful" means.

**Types of labels we build:**
- **Binary**: is this review in the top 50% useful? (yes/no)
- **Graded**: which usefulness tier is it in? (0 votes, 1-1, 2-4, 5-9, 10+)
- **Within-group percentile**: rank within its business/age group (0.0 = least useful, 1.0 = most useful)
- **Top-decile**: is this review in the top 10% most useful in its group?

**"Snapshot-safe"** means these labels only use information from the snapshot date — no future vote data.

---

### Stage 5: Feature-Usefulness Analysis Within Age Buckets
**What it does:** Checks whether features we might use for prediction (text length, star rating, user tenure, etc.) actually correlate with useful votes — when compared within the same age bucket.

**Why it matters:** Confirms that our features have predictive signal, and that the age-controlled approach doesn't destroy that signal.

---

### Stage 6: Pairwise/Listwise Training Data Feasibility
**What it does:** Calculates how many valid training pairs we can create for pairwise ranking.

**The formula:**
```
valid_pairs = C(n, 2) - tied_pairs
```
Where `C(n, 2)` = all possible pairs from n reviews, and `tied_pairs` = pairs where both reviews have the same useful vote count (ties can't be used to train a ranker).

**Why it matters:** If there aren't enough valid pairs, pairwise ranking won't work well.

---

### Stage 7: Leakage and Scope Check
**What it does:** A strict enforcement check — makes sure nothing illegal snuck into our analysis.

**Specifically checks:**
- `funny` and `cool` are NOT used as features
- No reviews from different age buckets were compared
- No outputs contain raw review text
- No markdown files claim we can track votes over time (we can't — it's a snapshot!)

---

### Stage 8: Summary Report
**What it does:** Writes a final Markdown summary of everything found in Stages 1-7.

**Output file:** `outputs/tables/track_b_s8_eda_summary.md`

---

## 5. Key Rules to Know

### The Banned Features: `funny` and `cool`
**Never use `funny` or `cool` as model features.** Here's why:

When a user writes a review, other users can vote it as "useful", "funny", or "cool" simultaneously. If someone reads a review and votes it "useful", they might also vote it "funny" — both votes happen at the same time.

If we use `funny` as a feature to predict `useful`, we're essentially using "what people voted at the same moment" to predict "what people voted at the same moment" — that's circular/leaky.

**Analogy:** Predicting how many people clap at the end of a speech using how many people cheered during it — both happened at the same time, so one can't predict the other.

### Why `snapshot_metadata.json` Must Be Read (Not Recomputed)
Each stage reads the snapshot date from `snapshot_metadata.json` rather than computing it themselves. This ensures all stages agree on the same reference date.

If each stage computed `MAX(review_date)` independently, there's a risk of slight inconsistencies (e.g., if some intermediate step filtered data differently). One source of truth = no confusion.

### No Cross-Age Comparisons
A 3-day-old review must NEVER be compared against a 2-year-old review when building training data. Always stay within age buckets.

---

## 6. The Code Structure

### `src/ingest/load_yelp_json.py`
Loads raw JSON into DuckDB. Same as Track A — this is the shared first step.

**Key function:** `run(config)` — extracts the tar archive, loads 5 entity tables.

---

### `src/validate/schema_checks.py`
Checks data quality after loading — null rates, date ranges, row counts.

**Key function:** `run(config)` — returns PASS/FAIL for each entity.

---

### `src/curate/build_review_fact.py`
Builds the fact table. For Track B, this also creates the `review_fact_track_b` view which adds the extra columns (`is_open`, `fans`, `elite`).

**Key outputs:**
- `data/curated/review_fact.parquet` — Track A's table
- `data/curated/review_fact_track_b.parquet` — Track B's table (with extra columns)
- `data/curated/snapshot_metadata.json` — the reference date JSON

---

### `src/eda/track_b/` (not yet implemented stages)
Each stage will live here as a separate Python file, e.g.:
- `src/eda/track_b/vote_distribution.py` — Stage 1
- `src/eda/track_b/age_confounding.py` — Stage 2
- etc.

All follow the same pattern as the Track A stage code.

---

## 7. Config Files

### `configs/base.yaml` — Shared settings
```yaml
paths:
  curated_dir: "data/curated"  # Where Parquet files live
  db_path: "data/yelp.duckdb"  # DuckDB database

ingestion:
  memory_limit_gb: 4   # RAM limit for DuckDB
  threads: 4           # Parallel threads
```

### `configs/track_b.yaml` — Track B specific settings
```yaml
snapshot:
  reference_date: "2022-01-19"   # The snapshot date

age_buckets:
  thresholds_days: [90, 180, 365, 730, 1825]
  labels: ["A: 0-90d", "B: 91-180d", "C: 181-365d",
           "D: 366-730d", "E: 731d-5y", "F: 5y+"]

ranking_groups:
  business:
    min_group_size: 5          # Need at least 5 reviews to rank
    min_distinct_useful: 2     # Need at least 2 different useful scores
  category_city:
    min_group_size: 10

leakage:
  banned_features:
    - "review.funny"   # NEVER use these
    - "review.cool"

quality:
  min_qualifying_groups: 1000  # Need 1000+ valid ranking groups
```

**To change a setting:** Edit the YAML and re-run the stage.

---

## 8. How to Run the Pipeline

```bash
# Step 1: Shared stages (same as Track A)
python scripts/run_pipeline.py --approach shared
# Or: ./run_pipeline.sh shared   (WSL/Linux)
# Or: .\run_pipeline.ps1 shared  (Windows)

# OR run shared stages individually:
python -m src.ingest.load_yelp_json --config configs/base.yaml
python -m src.validate.schema_checks --config configs/base.yaml
python -m src.curate.build_review_fact --config configs/base.yaml

# Step 2: Track B stages
python scripts/run_pipeline.py --approach track_b
# Or: ./run_pipeline.sh track_b

# OR run individual Track B stages:
python -m src.eda.track_b.vote_distribution --config configs/track_b.yaml
python -m src.eda.track_b.age_confounding --config configs/track_b.yaml
# ... etc for each stage
```

---

## 9. Glossary

| Term | Plain English |
|------|--------------|
| **EDA** | Exploratory Data Analysis — understanding your data before building a model |
| **Snapshot** | A frozen copy of the database at a specific point in time — like a photo, not a video |
| **Parquet** | A compressed, fast file format for tables (like a supercharged CSV) |
| **DuckDB** | A fast analytics database stored in a single file |
| **Exposure-time bias** | Older items have had more time to collect votes/views, making them look more popular even if they're not better |
| **Age bucket** | A group of reviews with similar "ages" (time since written) — used to compare apples to apples |
| **Learning-to-rank** | A type of ML that sorts/ranks items rather than predicting a single value |
| **Pairwise ranking** | Training a model by asking "is A better than B?" for many pairs |
| **Listwise ranking** | Training a model to rank an entire list at once |
| **Zero-inflated** | A distribution where most values are 0, with a long tail of non-zero values (most reviews have 0 useful votes) |
| **Confounding variable** | A hidden factor that causes a fake correlation. Review age confounds useful vote counts. |
| **Leakage** | Using data that wouldn't be available at prediction time — "cheating" |
| **Snapshot-safe label** | A label (answer key) computed only from data available at the snapshot date |
| **C(n, 2)** | The number of ways to pick 2 items from n items — used for counting pairs |
| **CLI** | Command-Line Interface — running programs from the terminal |
| **YAML** | A simple config file format (key: value pairs) |

---

## 10. Quick Start Checklist for Interns

- [ ] Read `CoWork Planning/yelp_project/track_b/CLAUDE.md` for quick reference
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run the shared pipeline first: `python scripts/run_pipeline.py --approach shared` or `./run_pipeline.sh shared`
- [ ] Verify `data/curated/snapshot_metadata.json` exists after curation
- [ ] Verify `data/curated/review_fact_track_b.parquet` exists
- [ ] Check `snapshot_metadata.json` — note the `snapshot_reference_date`
- [ ] Never use `funny` or `cool` as features (banned!)
- [ ] Always work within age buckets — never compare old reviews to new ones
- [ ] Check outputs in `outputs/figures/track_b_*` and `outputs/tables/track_b_*`

---

## 11. Common Questions (FAQ)

**Q: What if a business has only 2 reviews?**
It gets filtered out. We need at least 5 reviews per business group to make ranking meaningful (Stage 3).

**Q: Can I use "funny" or "cool" votes as a feature?**
NO. Absolutely not. Stage 7 will fail if you do. They're simultaneous-observation leakage.

**Q: Why age buckets instead of using review age as a continuous number?**
Age buckets let us explicitly control for age rather than hoping a model learns to. It's also safer — we compare only reviews within the same bucket, eliminating the confounder entirely.

**Q: What if most reviews have 0 useful votes?**
That's fine and expected (zero-inflated distribution). Stage 1 will document this. We can still learn from the non-zero reviews and the relative ranking within groups.

**Q: What if Stage 7 fails?**
Go back and fix whichever stage caused the violation. Re-run that stage, then re-run Stage 7.

**Q: When do I run Stage 8?**
After Stages 1-7 all complete successfully. Stage 8 reads all their outputs and compiles the final summary.

---

*Questions? Talk to your team lead. You've got this!*
