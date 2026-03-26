---
depends_on: [M002-c1uww6]
---

# M003-rdpeu4: Fairness audit and stronger modeling passes — Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

## Project Description

This milestone takes the baseline modeling layer and pushes it in two directions:

1. deliver Track E as an accountability layer by auditing at least one upstream model from Track A or Track D and applying one mitigation lever
2. compare stronger or combined model approaches only where they materially improve the framing-question answers

This is also the milestone where backup compute paths become relevant if the local Windows + RTX 3080 path is not enough.

## Why This Milestone

The project’s punchline is not just “we trained models.” It is “we measured, predicted, and audited platform trust.” That requires both stronger model comparisons and a fairness/accountability layer that can quantify tradeoffs instead of hand-waving them.

## User-Visible Outcome

### When this milestone is complete, the user can:

- show at least one stronger or combined model comparison against the established baselines
- demonstrate a Track E fairness audit on a real upstream model, including one mitigation lever and its accuracy tradeoff

### Entry point / environment

- Entry point: modeling/evaluation workflows defined after M002
- Environment: local dev first, with conditional escalation to Colab Pro or HPC if needed
- Live dependencies involved: local GPU runtime, optional SSH/HPC path if local results are insufficient

## Completion Class

- Contract complete means: stronger model comparisons exist where justified, and Track E has a real audit-plus-mitigation demonstration
- Integration complete means: the fairness audit attaches to a real upstream model rather than a synthetic example
- Operational complete means: heavier compute paths are only used if they materially improve the final report path

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- at least one upstream model from A or D is audited for disparity using Track E logic
- one mitigation lever changes the fairness-versus-accuracy profile in a measurable way
- stronger or combined model passes are justified by evidence, not just ambition

## Risks and Unknowns

- Track E can become vague unless the upstream target model is chosen explicitly
- Combined models can become expensive and unfocused if not tied to the framing questions
- HPC/Colab overflow can add setup drag if invoked prematurely

## Existing Codebase / Prior Art

- `src/eda/track_e/` — current fairness/disparity groundwork for later audit work
- M002 baseline outputs (to be created) — expected upstream models for fairness audit
- Existing repo planning that already frames Track E as an audit layer rather than a standalone predictor

## Relevant Requirements

- R009 — Deliver Track E as a fairness-audit baseline on an upstream Track A or D model, then demonstrate one mitigation lever
- R010 — Compare stronger or combined model approaches where they materially improve framing-question answers
- R022 — Enable Colab Pro and/or HPC overflow as a conditional fallback if local baseline quality or runtime is insufficient

## Scope

### In Scope

- fairness audit on an upstream model
- one mitigation lever and tradeoff measurement
- stronger or combined model passes where they materially help
- conditional compute overflow planning if needed

### Out of Scope / Non-Goals

- building a public-facing product
- multimodal future-works expansion beyond what the core semester path can honestly support

## Technical Constraints

- Track E stays attached to a real upstream model
- stronger modeling should answer framing questions, not become a detached benchmark exercise
- HPC/Colab should remain backup infrastructure unless local results force the issue

## Integration Points

- M002 baseline model outputs
- Track E disparity and mitigation logic from the current repo
- M004 downstream report, deck, and website storytelling

## Open Questions

- Should the first fairness audit target be Track A or Track D?
- Which mitigation lever is both credible and feasible within the semester window?
- What threshold of model gain justifies moving from baseline-only to stronger or combined approaches?
