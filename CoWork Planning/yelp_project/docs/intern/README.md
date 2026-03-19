# Intern Documentation Hub

Welcome! This folder contains beginner-friendly explanations of everything in the Yelp Open Dataset project. If you're new to the team, start here.

## How to Navigate

| Folder | What's Inside |
|---|---|
| `code/` | Explanations of Python scripts — what they do, how to run them, and key concepts |
| `workflows/` | Step-by-step guides for pipelines and processes |
| `config/` | What each configuration file means and how to change it |
| `decisions/` | Why the team chose specific tools, approaches, or designs |
| `GLOSSARY.md` | Definitions of every technical term used in this project |

## Where to Start

1. Read `GLOSSARY.md` first to get familiar with the vocabulary.
2. Read `workflows/` to understand how the project pipeline works end-to-end.
3. Look up specific scripts in `code/` when you need to understand or modify something.
4. Check `decisions/` when you want to know *why* something was done a certain way.

## Newest Docs

- `workflows/track_c_pipeline.md` explains the sentiment-and-topic drift pipeline.
- `workflows/track_d_pipeline.md` explains the cold-start recommender pipeline.
- `workflows/track_e_pipeline.md` explains the bias and disparity audit pipeline.
- `config/track_c_yaml.md`, `config/track_d_yaml.md`, and `config/track_e_yaml.md` explain the per-track settings.
- `code/track_c_modules.md`, `code/track_d_modules.md`, and `code/track_e_modules.md` explain the stage modules in plain English.
- `decisions/2026-03-13_track_cd_shared_contract.md` explains the shared artifact and leakage rules added with Tracks C and D.

## How These Docs Are Generated

These documents are automatically created and updated by the **Intern Documentation Agent** before every commit. The agent reviews what changed in the code and writes explanations targeted at your level.

If something is unclear or missing, ask the team — and we'll update these docs so the next person doesn't have the same question.

## Project Quick Reference

- **Dataset:** Yelp Open Dataset (business reviews, user profiles, tips, check-ins)
- **Goal:** 5 research tracks (A–E) — all implemented — exploring rating prediction, review usefulness, sentiment trends, recommendations, and fairness
- **Tech stack:** Python, DuckDB, Parquet, matplotlib/seaborn
- **Run any pipeline stage:** `python -m src.<module>.<script> --config configs/<config>.yaml`
