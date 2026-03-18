# Config: `configs/track_c.yaml`

> **Last updated:** 2026-03-13
> **Related commit:** Add Track C configuration
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../workflows/track_c_pipeline.md` first.

## The Big Picture

`configs/track_c.yaml` is the control panel for the sentiment-and-topic drift pipeline.

It answers questions like:

- How many reviews does a city need before we trust it?
- Should we aggregate by month or quarter?
- How much raw text should we sample for NLP profiling?

## How It Works (Step by Step)

### `geography`

- `min_city_reviews`: the minimum number of reviews a city needs to be treated as analyzable
- `top_n_cities`: how many cities get detailed charts

Why this matters: a trend in a tiny city can look dramatic just because the sample is small.

### `temporal`

- `bin_granularity`: whether the preferred time bucket is month or quarter
- `min_reviews_per_bin`: the minimum reviews needed inside one time bucket

Why this matters: very small bins create noisy sentiment averages.

### `nlp`

- `sentiment_engine`: which sentiment scorer to try first
- `sample_size`: how many reviews to sample for text-heavy stages
- `keyword_list`: the words Track C monitors over time
- `tfidf_*`: limits for the optional clustering summary

Why this matters: text work is expensive, so the config controls how much of the corpus you touch.

### `drift`

- `slope_p_threshold`: how strict the significance rule should be
- `rolling_window_months`: the window used for smoothing

Why this matters: these settings decide how easy it is to call something “drift.”

### `events`

- `inactivity_close_proxy_days`: how long a business can stay quiet before Track C treats it as a possible closure candidate

Why this matters: Yelp does not give exact close dates, so Track C uses a careful proxy instead.

### `quality`

- `sentiment_star_correlation_min`: minimum acceptable sanity-check correlation
- `min_analyzable_cities`: lower bound for a useful study

Why this matters: these settings stop interns from over-interpreting weak outputs.

## Common Questions

**Q: Why is there both monthly and quarterly output?**
A: Monthly is more detailed. Quarterly is more stable. The config lets the project compare both.

## Try It Yourself

```bash
python -m src.eda.track_c.geo_coverage --config configs/track_c.yaml
```
