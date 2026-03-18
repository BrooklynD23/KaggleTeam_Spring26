# Decision: Shared Contract for Tracks C and D

> **Last updated:** 2026-03-13
> **Related commit:** Add Track C/Track D shared artifacts, dispatcher wiring, and safety checks
> **Difficulty level:** Beginner

## What You Need to Know First

- Read `../GLOSSARY.md` for **semijoin**, **hard gate**, and **soft audit**.

## The Big Picture

Tracks C and D were added on top of the existing shared Yelp pipeline.

That sounds simple, but both tracks needed new safety rules:

- Track C needed safe access to raw text without leaking text into outputs.
- Track D needed strict time-based splits and a blocking leakage check.

## What Decision Was Made

The project added a stronger shared contract with four important pieces:

### 1. The dispatcher now knows about Track C and Track D

This means interns can run:

```bash
python scripts/run_pipeline.py --approach track_c
python scripts/run_pipeline.py --approach track_d
```

### 2. Shared curation now verifies more artifacts

The dispatcher now checks for:

- `user.parquet`
- `tip.parquet`
- `checkin.parquet`
- `checkin_expanded.parquet`

This matters because Track C and Track D depend on those files, and silent partial curation would create confusing downstream failures.

### 3. A new expanded check-in artifact was added

`checkin_expanded.parquet` turns one comma-separated string into one row per check-in date.

This is easier to analyze because time-series stages should not have to keep reparsing a text blob every time.

### 4. Track D now loads splits strictly

Track D uses a strict split loader that raises an error if the real Track A Stage 5 split artifact is missing.

This prevents “pretend evaluations” that accidentally use config placeholders.

## What Alternatives Were Considered

### Alternative 1: Let every track parse `checkin.parquet` for itself

Why it was rejected:

- repeated parsing code
- higher chance of inconsistent behavior
- harder for interns to debug

### Alternative 2: Let Track D use placeholder split dates quietly

Why it was rejected:

- easy to misuse
- would make experiments look valid when they are not

### Alternative 3: Make Track C’s text scan a hard gate too

Why it was rejected:

- Track C is descriptive EDA, not a prediction pipeline
- a summary that reports the problem is still useful during exploration

## What This Means for Your Work

- If you add a new shared artifact, register it in the dispatcher too.
- If you touch Track C text stages, keep the semijoin and “drop raw text before parquet” rule intact.
- If you touch Track D features, assume the leakage gate will inspect your work and block unsafe fields.

## Common Questions

**Q: Why is Track C a soft audit but Track D a hard gate?**
A: Track C’s main safety issue is accidental text exposure in analysis outputs. Track D’s main safety issue is invalid recommendation logic, which would make downstream modeling untrustworthy. The second problem is more severe, so it blocks.

## Try It Yourself

Generate the shared curated artifacts:

```bash
python scripts/run_pipeline.py --approach shared
```

Then check that the new artifact exists:

```bash
ls data/curated/checkin_expanded.parquet
```
