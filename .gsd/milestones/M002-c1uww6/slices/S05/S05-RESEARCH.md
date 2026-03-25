# S05 — Research

**Date:** 2026-03-23

## Summary

S05 is **targeted research**. The repo already has Track D EDA prerequisites and the shared modeling contract, but `src/modeling/track_d/` still has only `__init__.py` (no runtime baseline implementation).

Primary requirement alignment for this slice:
- **Owns/supports R008 (primary):** D1 cold-start baseline with explicit as-of popularity comparator.
- **Supports R009 + R012 (secondary):** clean upstream model evidence for downstream audit/story handoff.

Current repo reality relevant to S05:
- `outputs/modeling/track_d/` currently has only `.gitkeep` (no metrics/config/summary/scores/figure yet).
- D1/D2 EDA artifacts are present through Stage 8 (`outputs/tables/track_d_s2...s8_*.parquet`).
- Stage 7 is large but tractable if bounded:
  - `track_d_s7_eval_cohorts.parquet`: 100,000 rows
  - `track_d_s7_eval_candidate_members.parquet`: 9,970,188 rows (D1: 7,970,188; D2: 2,000,000)
- D1 label presence is limited (about 16.3% of candidate sets have a positive label), so metric denominator semantics must be explicit.

Per `debug-like-expert` (“verify, don’t assume”), existing EDA outputs are readiness signals, not baseline proof. S05 still needs executable modeling code + tests + artifacts.

## Recommendation

Implement `src/modeling/track_d/baseline.py` as a **D1-first ranking baseline** that:

1. Uses only existing as-of Track D artifacts (`s3`, `s4`, `s7`) and snapshot-safe features.
2. Trains one simple, reproducible pointwise scorer (same complexity posture as S02/S03/S04 baselines).
3. Evaluates against an explicit as-of popularity comparator with **Recall@20** and **NDCG@10**.
4. Emits the standard M002 artifact bundle under `outputs/modeling/track_d/`.
5. Keeps D2 strictly non-blocking via an explicit optional gate/report surface.

Skill-driven execution stance:
- `coding-standards`: KISS/YAGNI — avoid recommender stack expansion.
- `tdd-workflow` + `test`: helper-first regression tests before full run.
- `verification-loop`: end with explicit runtime and pytest verification, not file-presence assumptions.

## Implementation Landscape

### Key files

- `src/modeling/track_d/__init__.py` — package exists, runtime missing.
- `src/modeling/track_a/baseline.py` — best template for artifact contract structure.
- `src/modeling/track_b/baseline.py` — best template for grouped ranking metrics and comparator reporting.
- `src/modeling/README.md` — contract requiring metrics + scored artifact + config snapshot + summary.
- `configs/track_d.yaml` — D1/D2 thresholds, candidate size cap, K metrics, leakage constraints.
- `src/eda/track_d/popularity_baseline.py` — canonical as-of popularity logic to anchor comparator semantics.
- `src/eda/track_d/evaluation_cohorts.py` — canonical candidate-set and label construction semantics (D1/D2 split, bounded construction).
- `outputs/tables/track_d_s3_business_early_signals.parquet` — D1 candidate feature source.
- `outputs/tables/track_d_s4_popularity_baseline_asof.parquet` — explicit comparator source.
- `outputs/tables/track_d_s7_eval_cohorts.parquet` + `track_d_s7_eval_candidate_members.parquet` — evaluation task surface.
- `tests/test_track_a_baseline_model.py`, `tests/test_track_b_baseline_model.py`, `tests/test_track_c_baseline_model.py` — expected modeling test style.

### Natural seams for planner decomposition

1. **Runtime seam (required):**
   - Add `src/modeling/track_d/baseline.py` with run/CLI/artifact writers.
2. **Evaluation seam (required):**
   - D1 metrics + explicit popularity comparator (Recall@20/NDCG@10).
3. **Optional gate seam (required boundary, optional execution):**
   - D2 reported as optional/stretch surface, never milestone blocker.
4. **Test seam (required):**
   - New `tests/test_track_d_baseline_model.py` for helper and contract behavior.

### Suggested build order

1. **Implement D1 data assembly helpers**
   - Join D1 candidate members (`subtrack='D1'`) to D1 candidate features (Stage 3) and popularity stats (Stage 4).
   - Keep strict as-of joins using `(candidate_business_id, as_of_date)`.

2. **Implement scoring + comparator evaluation**
   - One simple pointwise model (e.g., HGB classifier/regressor) for candidate ranking.
   - Comparator must remain explicit as-of popularity (not implicit row order).
   - Report both:
     - metric-on-labeled-sets (retrieval-valid denominator), and
     - label-coverage rate (to avoid denominator ambiguity).

3. **Implement artifact bundle writing**
   - `outputs/modeling/track_d/metrics.csv`
   - `outputs/modeling/track_d/scores_test.parquet` (or equivalent scored output)
   - `outputs/modeling/track_d/config_snapshot.json`
   - `outputs/modeling/track_d/summary.md`
   - `outputs/modeling/track_d/figures/<d1_figure>.png`

4. **Implement optional D2 gate/report marker**
   - Default non-blocking behavior in code and summary wording.
   - If no D2 attempt, write explicit “not attempted in S05, optional” status in summary/config snapshot.

5. **Add tests and run verification**
   - Helper-level tests first, then runtime/artifact verification.

## Constraints

- D1 and D2 stay separate in all outputs and logic.
- D2 cannot become a milestone-completion dependency in S05.
- No banned leakage fields (`business.stars`, `business.review_count`, `business.is_open`, user lifetime snapshots).
- No raw review text in modeling artifacts.
- Use config-driven paths/thresholds only (no hardcoded repo paths).
- Keep output contract under `outputs/modeling/track_d/` only.

## Common Pitfalls

- **Comparator ambiguity:** using candidate row order instead of explicit as-of popularity features/ranks.
- **Metric denominator confusion:** computing Recall@20/NDCG@10 over unlabeled sets without also exposing label coverage.
- **Scope creep:** adding full D2 training path in S05 instead of enforcing optional gate semantics.
- **Cross-subtrack mixing:** accidental D2 rows in D1 training/eval joins.
- **Heavy runtime blowup:** unbounded training over ~8M D1 rows without deterministic caps.

## Verification Approach

Planned verification sequence for executors:

1. **Unit/regression tests (new + existing):**
   - `python -m pytest tests/test_track_d_baseline_model.py`
   - `python -m pytest tests/test_m002_modeling_contract.py tests/test_track_d_cohorts.py`

2. **Runtime baseline execution:**
   - `python -m src.modeling.track_d.baseline --config configs/track_d.yaml`

3. **Artifact contract checks:**
   - Verify existence/content of metrics, scored output, config snapshot, summary, figure under `outputs/modeling/track_d/`.
   - Verify summary explicitly states D1 required path and D2 optional/non-blocking status.

4. **Comparator sanity checks:**
   - Confirm metrics include model vs explicit as-of popularity comparator at NDCG@10 and Recall@20.

## Resume Notes (interrupted check)

One in-progress diagnostic was interrupted by the context-budget stop while checking candidate-feature join coverage for D1 (`s7` members joined to `s3` early signals). Resume with a one-shot check before training to confirm non-null coverage for selected D1 features.

Recommended resume command:

```bash
python - <<'PY'
import pandas as pd
m = pd.read_parquet('outputs/tables/track_d_s7_eval_candidate_members.parquet')
m = m[m.subtrack=='D1'][['candidate_business_id','as_of_date','is_label']]
s3 = pd.read_parquet('outputs/tables/track_d_s3_business_early_signals.parquet')
df = m.merge(s3, left_on=['candidate_business_id','as_of_date'], right_on=['business_id','as_of_date'], how='left')
print('join_coverage', df['business_id'].notna().mean())
print('feature_non_null', df[['prior_review_count','price_range','attribute_count','prior_review_mean_stars','prior_tip_count','prior_checkin_count']].notna().mean())
PY
```

## Skills Discovered

Core technology skill candidates found (not installed):

- scikit-learn: `npx skills add davila7/claude-code-templates@scikit-learn`
- duckdb: `npx skills add silvainfm/claude-skills@duckdb`
- pandas: `npx skills add jeffallan/claude-skills@pandas-pro`
