# Project Glossary

Every technical term used in this project, explained in plain English. Updated automatically before each commit.

---

### As-Of Feature
**Plain English:** A feature (input to a model) that only uses information that was available *at that point in time*. You can't use tomorrow's data to make today's prediction.
**In our project:** When we compute "how many reviews did this user write before this review," we only count reviews with earlier dates. We never peek at future data.
**Example:** For a review written on March 5, the user's prior review count only includes reviews from March 4 and earlier.

### CLI (Command-Line Interface)
**Plain English:** Running a program by typing a command in a terminal instead of clicking buttons in a GUI.
**In our project:** Every pipeline stage runs via a command like `python -m src.eda.track_a.temporal_profile --config configs/track_a.yaml`.
**Example:** Open a terminal, type the command, press Enter. The program runs and saves its output to files.

### Cold Start
**Plain English:** The problem of making predictions about something you have little or no history for — like recommending restaurants to a brand-new user.
**In our project:** Track D specifically studies this. A "cold-start user" has zero or very few prior reviews. A "cold-start business" is newly listed.
**Example:** If a user just signed up and hasn't reviewed anything, we can't compute their average rating — there's nothing to average.

### Curated Table
**Plain English:** A cleaned-up, ready-to-use version of raw data. Think of it as the organized spreadsheet you make from a messy data dump.
**In our project:** `review_fact` is our main curated table — it combines review data with business and user information, pre-filtered and pre-joined so every analysis stage can use it directly.
**Example:** Instead of joining three raw tables every time you run a query, you use `review_fact` which already has the joins done.

### DuckDB
**Plain English:** A lightweight database engine that runs inside your Python script — no server needed. It's great for analyzing large datasets quickly.
**In our project:** We load Yelp's JSON files into DuckDB, then run SQL queries against them. DuckDB can handle our 4+ GB dataset without running out of memory.
**Example:** `con = duckdb.connect("data/yelp.duckdb")` opens the database. Then you run SQL: `con.execute("SELECT COUNT(*) FROM review")`.

### EDA (Exploratory Data Analysis)
**Plain English:** The phase where you look at your data before building any models. You're answering questions like: "How much data do we have? Are there missing values? What patterns exist?"
**In our project:** Each track (A through E) has an EDA pipeline with 8 stages that profile the data, check for problems, and prepare for modeling.
**Example:** Track A's Stage 1 creates histograms of star ratings over time to see if ratings have gotten higher or lower over the years.

### Feature
**Plain English:** One piece of information you give to a model to help it make predictions. Think of features as the "columns" in a spreadsheet that the model reads.
**In our project:** Examples include text length (word count of a review), user tenure (how long someone has been on Yelp), and business category.
**Example:** If you're predicting a star rating, the model might use features like "this user's average past rating is 3.8" and "this business usually gets 4.2 stars."

### Leakage (Data Leakage)
**Plain English:** Accidentally giving your model information it shouldn't have — like letting a student see the answer key during a test. The model looks great in testing but fails in real life.
**In our project:** The biggest leakage risk is using `business.stars` (the average star rating across ALL reviews, including future ones) as a feature when predicting a single review's stars.
**Example:** If we're predicting a 2019 review's rating and we use the business's overall average (which includes 2020 and 2021 reviews), that's leakage.

### NDJSON (Newline-Delimited JSON)
**Plain English:** A file format where each line is a separate JSON object. Like a list of records, one per line.
**In our project:** The Yelp dataset comes in this format. Each line in `yelp_academic_dataset_review.json` is one review.
**Example:** Line 1: `{"review_id": "abc", "stars": 5, "text": "Great place!"}`, Line 2: `{"review_id": "def", "stars": 2, "text": "Not good."}`.

### Parquet
**Plain English:** A file format designed for storing large datasets efficiently. It compresses well and reads fast because it stores data by column rather than by row.
**In our project:** After loading Yelp's JSON into DuckDB, we export curated tables as `.parquet` files in `data/curated/`. Any tool can read these.
**Example:** `review_fact.parquet` in `data/curated/` is the main analytical table that all tracks use.

### Temporal Split
**Plain English:** Dividing your data by time — older data for training, newer data for testing. This simulates real life where you can only train on the past.
**In our project:** We pick two dates, T1 and T2. Data before T1 = training. T1 to T2 = validation. After T2 = testing. The model never sees future data during training.
**Example:** If T1 = June 2019 and T2 = September 2020, the model trains on all reviews before June 2019.

### Window Function
**Plain English:** A SQL feature that lets you calculate something across a group of rows related to the current row — like a running total or a ranking within a group.
**In our project:** We use an **aggregate-then-lag** pattern to compute as-of features rather than an `ORDER BY review_date` window, because same-day reviews would otherwise be counted ambiguously. First we aggregate daily review counts per user, then we use `LAG()` to look up the prior-day totals — ensuring that no reviews written on the same day as the target review are counted as "prior."
**Example:** For user #123's review on March 5, we aggregate all their reviews through March 4 into a daily summary, then read the March 4 running total via `LAG()`. Any other reviews they wrote on March 5 are excluded from the count.

### Zero Inflation
**Plain English:** When most values in a dataset are zero. Like if you asked 100 people how many skydiving trips they took last year — 95 would say zero.
**In our project:** The `useful` vote count in Track B is heavily zero-inflated. About 60-70% of reviews have zero useful votes.
**Example:** Out of 7 million reviews, roughly 4.5 million have `useful = 0`. This makes raw vote counts a poor regression target.

### Candidate Set
**Plain English:** The list of options a recommender is allowed to choose from at one decision point.
**In our project:** Track D builds candidate sets for D1 and D2, then checks whether the business a user actually chose appears inside that list.
**Example:** If a user is being recommended Phoenix restaurants, the candidate set might be the top 100 businesses in the same city and category.

### Drift Detection
**Plain English:** Looking for a trend that changes over time instead of staying flat.
**In our project:** Track C uses sentiment and keyword time series to flag cities where review language seems to be moving in a meaningful direction.
**Example:** If reviews in one city mention “delivery” more and more each quarter, that is a topic drift signal.

### Hard Gate
**Plain English:** A check that blocks the pipeline from continuing when it fails.
**In our project:** Track D Stage 8 is a hard gate. If it finds leakage, the pipeline raises an error instead of quietly writing a summary.
**Example:** If a Track D table contains a banned field like `business.stars`, the leakage check stops the run immediately.

### Language Detection
**Plain English:** Guessing what language a piece of text is written in.
**In our project:** Track C profiles review text to see whether most reviews are English and whether there are enough non-English reviews to matter for preprocessing.
**Example:** A review written in Spanish should be counted in the language summary instead of being treated as normal English text.

### Semijoin
**Plain English:** A filtering step where you keep rows from one table only if they match IDs in another table.
**In our project:** Track C reads raw text from `review.parquet`, but it semijoins against `review_fact.parquet` so it only touches reviews already approved for the curated analysis scope.
**Example:** “Load text for review IDs that exist in `review_fact`” is a semijoin pattern.

### Soft Audit
**Plain English:** A safety check that reports problems but does not stop the program.
**In our project:** Track C’s summary report scans parquet schemas for raw-text columns and reports problems in the markdown summary, but it does not raise an exception.
**Example:** If a Track C output accidentally includes a `text` column, the audit can mark it as a failure in the report while still letting you inspect the rest of the artifacts.
