# Track E README

## Focus

Track E studies bias, disparity, and fairness risks across neighborhoods, categories, and related subgroup definitions.

Primary question:

> What patterns of bias or disparity appear in ratings and recommendations across neighborhoods or business categories, and how can models be constrained or corrected?

## Current Status

- Planning folder exists and is set up.
- Implementation folder exists at `src/eda/track_e/` with 9 EDA stage modules.
- Pipeline is wired into the dispatcher and can be run via `python scripts/run_pipeline.py --approach track_e`.

## Key Documents

- [Track E pipeline spec](06_EDA_Pipeline_Track_E_Bias_Disparity.md)
- [Track E agent guide](AGENTS.md)
- [Track E Claude context](CLAUDE.md)
- [Top-level repo README](../../../README.md)

## Implementation Area

Code location: `src/eda/track_e/`

## Expected Deliverables

Track E planning calls for:

- Subgroup definition and coverage profiling artifacts
- Star and usefulness disparity tables
- Imbalance and proxy-risk analysis
- Baseline fairness metrics and mitigation candidates
- Final summary markdown report

## Implementation Notes

- 9 stage modules: subgroup_definition, coverage_profile, star_disparity, usefulness_disparity, imbalance_analysis, proxy_risk, fairness_baseline, mitigation_candidates, summary_report.
- Config: `configs/track_e.yaml`
- Output artifacts: `outputs/tables/track_e_*`, `outputs/figures/track_e_*`, `outputs/logs/track_e_*`
