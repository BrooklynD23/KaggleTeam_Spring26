# Track C — Agent Configuration: Sentiment and Topic Drift

## Agent Purpose

This agent implements the EDA pipeline for **Track C: detecting sentiment and topic drift over time across cities**. It is a geo-temporal NLP profiling agent — it does not train topic models or fit time-series models.

## Context

You are working on a semester-scale data science project using the **Yelp Open Dataset**. Track C asks: *How does sentiment and topic prevalence shift over time across cities/neighborhoods, and what events or business changes correlate with those shifts?*

Your job is to execute the EDA pipeline defined in `04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md`. Read that file first.

## Agent Responsibilities

1. **Map** geographic coverage — identify which cities have enough reviews to analyze.
2. **Bin** reviews temporally (monthly/quarterly) and profile volume over time.
3. **Compute** sentiment proxies (TextBlob/VADER) and validate against star ratings.
4. **Profile** keyword/topic prevalence over time per city using lightweight methods.
5. **Detect** drift — flag cities/periods with significant sentiment or topic shifts.
6. **Identify** candidate events (business openings/closings, check-in volume changes) that correlate with drift.

## Key Constraints

- All geographic outputs use **city-level or neighborhood-level aggregation** (never individual business or review level for public outputs).
- Enforce **minimum review count per bin** before computing aggregates (avoid noisy small-sample estimates).
- Include closed businesses in temporal analysis (avoid survivorship bias).
- Sentiment proxy must be validated against star ratings before trusting it.
- Outputs are aggregate-only. No raw review text in figures or tables.
- CLI-first: `python -m src.eda.track_c.<stage> --config configs/track_c.yaml`.

## Data Entities Needed

- `review` — text, stars, date, business_id
- `business` — city, state, categories, is_open, lat/lon
- `checkin` — timestamps per business
- `tip` — supplementary text signal

## Completion Signal

EDA is done when `outputs/tables/track_c_s9_eda_summary.md` exists and all exit criteria are met.
