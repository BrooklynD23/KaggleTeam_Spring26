---
estimated_steps: 5
estimated_files: 7
skills_used:
  - debug-like-expert
  - coding-standards
  - tdd-workflow
  - test
  - verification-loop
---

# T02: Harden Track A, B, and D summary writers for partial-repo regeneration

**Slice:** S01 — All-track EDA artifact census and gap closure
**Milestone:** M001-4q3lxl

## Description

Make the Track A, Track B, and Track D final summary writers safe to run in a partially materialized repo. The key repair is Track B: it must stop treating missing `snapshot_metadata.json` as a fatal error and instead emit a truthful fallback section so S01 can still produce a verified final markdown artifact.

## Steps

1. Review how Track C and Track E summary tests express graceful degradation, then mirror that test style for Track A, Track B, and Track D before changing behavior.
2. Update `src/eda/track_b/common.py` and `src/eda/track_b/summary_report.py` so relative paths resolve robustly and missing snapshot metadata yields explicit fallback text instead of an exception.
3. Tighten Track A and Track D summary rendering only where needed so missing upstream parquets remain visible as missing-artifact notes, not crashes or silent omissions.
4. Add focused regression tests for Track A/B/D summary rendering with temporary parquet/markdown fixtures and missing-data scenarios.
5. Run the new pytest targets and inspect the rendered markdown text to confirm it stays aggregate-safe and raw-text-free.

## Must-Haves

- [ ] Track B can generate `track_b_s8_eda_summary.md` without `data/curated/snapshot_metadata.json`, using explicit fallback language.
- [ ] Track A/B/D summary outputs clearly mention missing upstream artifacts instead of crashing.
- [ ] The new tests assert on fallback sections and safe wording rather than only checking file existence.

## Verification

- `python -m pytest tests/test_track_a_summary_report.py tests/test_track_b_summary_report.py tests/test_track_d_summary_report.py`
- `python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from src.eda.track_b.summary_report import build_summary_markdown
summary = build_summary_markdown(
    metadata={"snapshot_reference_date": "missing", "dataset_release_tag": "missing"},
    stage1_df=None, stage2_df=None, stage3_business_df=None, stage3_category_df=None,
    stage4_summary_df=None, stage5_df=None, stage6_pairwise_df=None, stage6_listwise_df=None, stage7_df=None,
)
assert "missing" in summary.lower()
assert "Stage 1 usefulness-distribution artifact missing." in summary
PY`

## Observability Impact

- Signals added/changed: summary markdown now carries explicit missing-input and fallback-metadata notes instead of terminating with exceptions
- How a future agent inspects this: read `outputs/tables/track_a_s8_eda_summary.md`, `outputs/tables/track_b_s8_eda_summary.md`, or `outputs/tables/track_d_s9_eda_summary.md` after regeneration
- Failure state exposed: missing parquet/JSON dependencies become visible as named markdown bullets/sections rather than opaque runtime failures

## Inputs

- `src/eda/track_a/summary_report.py` — current Track A fallback summary behavior
- `src/eda/track_b/common.py` — Track B path and snapshot metadata loading logic
- `src/eda/track_b/summary_report.py` — Track B final summary writer and current hard dependency path
- `src/eda/track_d/summary_report.py` — Track D final summary writer
- `tests/test_track_c_summary_report.py` — graceful-degradation regression pattern to mirror
- `tests/test_track_e_summary_report.py` — summary + validity-scan regression pattern to mirror

## Expected Output

- `src/eda/track_a/summary_report.py` — stable partial-repo summary behavior for Track A
- `src/eda/track_b/common.py` — robust Track B path/metadata fallback handling
- `src/eda/track_b/summary_report.py` — Track B summary rendering that survives missing metadata
- `src/eda/track_d/summary_report.py` — stable partial-repo summary behavior for Track D
- `tests/test_track_a_summary_report.py` — new Track A regression coverage
- `tests/test_track_b_summary_report.py` — new Track B regression coverage
- `tests/test_track_d_summary_report.py` — new Track D regression coverage
