# M003-rdpeu4: Fairness audit and stronger modeling passes

**Vision:** Prove the trust-marketplace accountability layer on real upstream predictions (audit + mitigation), then run disciplined stronger/combined model comparisons only where they materially improve framing-question answers, with compute escalation kept conditional.

## Success Criteria

- A real upstream model (Track A default, Track D optional secondary) is audited with model-aware fairness metrics tied to actual predictions.
- One mitigation lever is executed and reported with an authoritative pre/post fairness-vs-accuracy delta artifact.
- Stronger/combined modeling comparisons produce a decision-ready materiality table (gain, runtime cost, adopt/do-not-adopt).
- The milestone closes with one integrated rerun gate that regenerates M003 evidence artifacts for M004 handoff.
- Compute overflow remains conditional: either local sufficiency is proven or overflow is triggered with explicit evidence.

## Current Worktree Baseline

- M002 is marked complete and claims reproducible baseline modeling outputs plus contract tests for Track A/B/C/D1.
- Existing Track E code is primarily data-level disparity EDA; model-bound fairness audit surfaces are not yet the dominant runtime pattern.
- Orchestration is EDA-centric; M003 work should prefer explicit modeling/fairness commands and avoid broad dispatcher churn unless necessary.
- Guardrails already exist and should be reused: no raw text outputs, strict as-of leakage rules, no demographic inference, and config-driven paths.

## Key Risks / Unknowns

- **Integration truth risk:** if upstream scored artifacts are absent or unstable, all downstream fairness/mitigation claims fail.
- **Fairness vagueness risk:** Track E can remain descriptive unless explicitly bound to model predictions.
- **Mitigation-theater risk:** a mitigation claim without measurable pre/post tradeoff is not credible.
- **Model-zoo risk:** stronger-model experimentation can sprawl without a materiality gate.
- **Premature infra drag:** Colab/HPC setup can consume time without evidence that local execution is insufficient.

## Proof Strategy

- Retire integration-truth risk first by shipping a reproducible upstream intake contract as a real artifact bundle consumed by all later slices.
- Retire fairness vagueness and mitigation-theater risks by shipping executable audit and mitigation outputs with machine-readable schemas and threshold flags.
- Retire model-zoo risk by encoding a materiality gate into the stronger-model comparator output.
- Retire infra-drag risk at closeout with measured escalation triggers and an explicit `local_sufficient` vs `overflow_required` decision artifact.

## Verification Classes

- **Contract verification:** schema and threshold checks for intake, fairness audit outputs, mitigation deltas, and comparator outputs.
- **Integration verification:** end-to-end command execution from upstream baseline artifacts through final M003 closeout bundle.
- **Operational verification:** runtime-cost and escalation-trigger evidence proving local sufficiency or justified overflow usage.
- **Failure-visibility verification:** machine-readable pass/fail flags for fairness thresholds, mitigation deltas, and materiality gates.

## Milestone Definition of Done

This milestone is complete only when all are true:

- all slice deliverables are complete
- a real upstream model is audited with model-aware fairness metrics on real predictions
- one mitigation lever is executed with baseline vs mitigated fairness and accuracy deltas in a single authoritative artifact
- stronger/combined comparisons are run through a materiality gate and produce explicit adoption decisions
- an integrated M003 closeout rerun regenerates all required evidence artifacts
- compute escalation is explicitly resolved as either local sufficiency or evidence-backed overflow execution
- M003 outputs are cleanly consumable by M004 reporting/showcase work without handoff reconstruction

## Requirement Coverage

### Primary mapping

| Requirement | Disposition | Primary owner | Supporting slices | Notes |
|---|---|---|---|---|
| R009 | mapped | S02 | S01, S03, S05 | Core accountability deliverable: audit + mitigation on real upstream model.
| R010 | mapped | S04 | S01, S05 | Stronger/combined models only where material by explicit gate.
| R022 | mapped (conditional) | S05 | S04 | Overflow compute only if measured trigger criteria are breached.
| R012 | mapped (continuity support) | S05 | S02, S03, S04 | M003 evidence must flow cleanly into M004 trust-story deliverables.
| R011 | deferred to M004 | M004 | S05 (handoff-only support) | M003 does not implement showcase system; it produces handoff-ready evidence.

### Coverage summary

- Mapped in this milestone: **R009, R010, R022, R012 (supporting continuity)**
- Deferred with explicit owner milestone: **R011 → M004**
- Blocked: **none**
- Out of scope without owner: **none**

## Slices

- [x] **S01: Upstream audit-intake contract on reproducible scored artifacts** `risk:high` `depends:[]`
  > After this: the team can regenerate a validated upstream scored-intake bundle (Track A default) with required IDs, split/as-of marker, truth/prediction fields, and subgroup join keys that downstream fairness and comparator work can consume without ad hoc repair.

- [x] **S02: Model-aware fairness audit runtime on upstream predictions** `risk:high` `depends:[S01]`
  > After this: stakeholders can open a fairness audit bundle and see per-subgroup fairness metrics, disparities, support counts, and paired accuracy context computed from real upstream predictions (not data-only disparity proxies).

- [x] **S03: One mitigation lever with pre/post fairness-accuracy deltas** `risk:high` `depends:[S02]`
  > After this: stakeholders can inspect one authoritative pre/post table showing baseline vs mitigated fairness and accuracy metrics, signed deltas, and explicit threshold pass/fail outcomes.

- [x] **S04: Stronger/combined comparator with materiality gate** `risk:medium` `depends:[S01,S02]`
  > After this: stakeholders can inspect a comparator artifact with baseline metric, stronger/combined metric, delta, runtime cost, and material-improvement boolean that governs adoption decisions.

- [x] **S05: Integrated closeout gate with conditional compute-escalation decision** `risk:medium` `depends:[S01,S02,S03,S04]`
  > After this: one integrated M003 rerun regenerates audit, mitigation, and comparator evidence and emits an explicit escalation decision (`local_sufficient` or `overflow_required`) backed by measured trigger criteria, producing a clean M004 handoff surface.

### Remediation slices (added by validation round 0)

- [x] **S06: Fairness-signal sufficiency replay on real upstream predictions** `risk:high` `depends:[S01,S02]`
  > After this: S02 rerun evidence includes non-empty subgroup/disparity signal (or an explicitly approved fallback subgroup strategy) with contract-valid diagnostics that make S03 mitigation evaluation materially executable.

- [x] **S07: Mitigation ready-path delta closure + closeout rerun** `risk:high` `depends:[S03,S04,S05,S06]`
  > After this: S03 produces a non-empty authoritative pre/post fairness-vs-accuracy delta artifact, and S05 rerun resolves milestone closeout to `ready_for_handoff` with explicit mitigation/comparator/escalation evidence consumable by M004 without caveated reconstruction.

## Boundary Map

### S01 → S02

Produces:
- stable upstream scored-intake schema for fairness auditing
- reproducible intake-generation command surface
- schema guardrails for required fields and joinability

Consumes:
- M002 upstream baseline outputs and contracts

### S01 → S03

Produces:
- canonical baseline prediction intake used as mitigation baseline reference
- validated subgroup-linkable evaluation surface

Consumes:
- M002 upstream baseline outputs and contracts

### S01 → S04

Produces:
- baseline metric/runtime anchors for stronger-model materiality comparisons
- stable shared IDs/splits for fair candidate comparison

Consumes:
- M002 upstream baseline outputs and contracts

### S02 → S03

Produces:
- fairness metric definitions and subgroup disparity outputs used for mitigation targeting
- threshold flags that define baseline fairness posture

Consumes from S01:
- upstream scored-intake contract

### S02 → S05

Produces:
- model-bound fairness artifact bundle required for integrated closeout

Consumes from S01:
- upstream scored-intake contract

### S03 → S05

Produces:
- mitigation pre/post fairness-accuracy delta artifact
- mitigation outcome summary with explicit tradeoff statement

Consumes from S02:
- baseline fairness posture and subgroup metrics

### S04 → S05

Produces:
- stronger/combined model materiality decision artifact (gain + runtime + adoption boolean)

Consumes from S01:
- baseline comparison anchors

Consumes from S02:
- fairness context needed to prevent metric-only adoption decisions

## Planned Observability Surfaces

- M003 contract/integration pytest surfaces for intake, fairness audit, mitigation deltas, and comparator gates.
- `outputs/modeling/...` artifact bundles for fairness, mitigation, stronger-model comparison, and integrated closeout.
- One M003 closeout summary markdown linking authoritative artifacts and escalation disposition.

## Out-of-Scope Guardrails

- No standalone Track E predictor track.
- No unconstrained benchmark/model-zoo expansion.
- No mandatory Colab/HPC migration absent trigger evidence.
- No M004 website/report implementation inside M003.
