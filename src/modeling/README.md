# Modeling Contract

This package is the canonical code surface for M002 baseline modeling.

## Package Layout

- `src/modeling/common/` — shared helpers used by multiple tracks when the seam is real
- `src/modeling/track_a/` — Track A temporal future-star baseline
- `src/modeling/track_b/` — Track B snapshot usefulness baseline
- `src/modeling/track_c/` — Track C monitoring/drift baseline
- `src/modeling/track_d/` — Track D cold-start baseline

Do not place new M002 baseline code directly under `src/eda/`. EDA remains the analytical handoff layer; baseline implementation belongs here.

## Output Contract

Each required track must write outputs under `outputs/modeling/<track>/`.

Required files per track:

1. `summary.md`
2. `metrics.csv` or `metrics.parquet`
3. `config_snapshot.json`
4. at least one diagnostic figure or table
5. a documented reproducible command in `summary.md`

## Summary Contract

Each `summary.md` should include:

- task definition
- input surfaces used
- feature families used
- prohibited features explicitly excluded
- baseline model family
- trivial comparator
- metrics
- short interpretation
- known limitations
- M003 audit suitability note

## Scope Guardrails

- Track A and Track D must preserve as-of semantics and banned snapshot-only fields.
- Track B remains a snapshot-only ranking lane and must not drift into vote-growth prediction.
- Track C remains a monitoring/drift lane and must not claim forecasting scope in M002.
- Track D1 is required for M002; Track D2 is optional/stretch only.
- Track A is the preferred default M003 fairness-audit target unless Track D proves materially cleaner and stronger.
