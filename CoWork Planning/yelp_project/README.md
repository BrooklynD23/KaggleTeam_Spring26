# Yelp Open Dataset — Semester-Scale Data Science Project

## Package Contents

This package contains the planning documents for a five-track data science project using the Yelp Open Dataset. All documents are frameworks and pipeline specifications — no implementation code is included. These materials are intended for **internal academic use** within the course team/instructor context and are designed to be handed off to Claude Code agents for execution.

### Master PRD

| File | Description |
|---|---|
| `01_PRD_Yelp_Open_Dataset.md` | Central product requirements document covering all five research tracks, data architecture, governance, evaluation philosophy, and semester roadmap. |

### Track-Specific EDA Pipelines

Each track folder contains three files:

| File | Purpose |
|---|---|
| `*_EDA_Pipeline_*.md` | Full EDA pipeline specification with stages, CLI commands, outputs, quality checks, leakage audits, and exit criteria. |
| `AGENTS.md` | Agent configuration — responsibilities, constraints, data needs, and completion signals for the Claude Code agent assigned to this track. |
| `CLAUDE.md` | Quick-reference context sheet for the agent — framing question, pipeline stages, critical rules, and tech stack. |

### Track Index

| Folder | Track | Question |
|---|---|---|
| `track_a/` | A — Future Star Rating Prediction | How well can review text, user history, and business attributes predict future star ratings under strict time-split evaluation? |
| `track_b/` | B — Usefulness Ranking | At a fixed dataset snapshot, can you rank comparatively useful reviews after controlling for review age? |
| `track_c/` | C — Sentiment & Topic Drift | How does sentiment and topic prevalence shift over time across cities/neighborhoods? |
| `track_d/` | D — Cold-Start Recommender | Can separate business-cold-start and user-cold-start recommenders outperform as-of popularity baselines? |
| `track_e/` | E — Bias & Disparity | What patterns of bias or disparity appear in ratings and recommendations across neighborhoods or categories? |

## Shared Conventions

All tracks follow these conventions (detailed in the PRD):

- **CLI-first**: `python -m src.<module>.<script> --config configs/<config>.yaml`
- **Config-driven**: shared base config + per-track overrides
- **Parquet warehouse**: raw → interim → curated pipeline
- **Temporal splits**: strict chronological train/val/test for predictive temporal tracks; documented exceptions must be explicit
- **Aggregate-only outputs**: no raw review text in shared academic artifacts
- **Internal academic use only**: no public dashboard, portfolio demo, or row-level data sharing
- **As-of feature construction**: features at time *t* use only data before *t*

## How to Use with Claude Code

1. Set up the repo structure as described in the PRD (Section 16).
2. Place Yelp JSON files in `data/raw/`.
3. Assign one Claude Code agent per track using the `AGENTS.md` and `CLAUDE.md` in each track folder.
4. Run shared ingestion/curation stages first (defined in the PRD and referenced as Stage 0 in each pipeline).
5. Run per-track EDA stages in order.
6. Check exit criteria in each pipeline spec before proceeding to modeling.
