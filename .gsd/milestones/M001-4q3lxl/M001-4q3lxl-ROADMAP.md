# M001-4q3lxl: EDA completion, evidence packaging, and planning handoff

**Vision:** Turn the existing Yelp repo into a clean, verified handoff from implemented EDA code to semester-ready evidence, export packaging, and agent-ready planning — all in service of the trust-marketplace story: prediction, surfacing, monitoring, onboarding, and accountability.

## Success Criteria

- Tracks A, B, C, D, and E each have a verified final EDA summary artifact and a clear completeness status grounded in actual repo outputs
- The repo exposes aggregate-safe JSON/CSV/PNG/MD export surfaces that later milestones can use for modeling evidence, the final report, and the local-hosted website
- The planning layer includes distinct feature-plan folders, sprint subfolders, and phase docs detailed enough for downstream implementation agents to execute without re-scoping
- The trust-marketplace narrative and the intern-explainer workflow are documented in repo planning and aligned with the actual track outputs
- A final local handoff verification proves the EDA outputs, export contract, and planning structure are consistent enough for M002 baseline modeling to begin

## Key Risks / Unknowns

- Implemented-vs-materialized mismatch — some tracks have code wired into the dispatcher without clearly visible final summary artifacts, which can hide real readiness gaps
- Story fragmentation — five track outputs can still fail the final demo if they are not connected to the “trust marketplace” business narrative
- Export contract mismatch — the later website and report flow will be fragile if export packaging is improvised or inconsistent across tracks
- Agent planning drift — sprint and phase docs will be wasted motion if they are not anchored to the current repo, current outputs, and actual track rules

## Proof Strategy

- Implemented-vs-materialized mismatch → retire in S01 by proving which final track artifacts already exist, which are missing, and which were repaired into a complete five-track EDA set
- Export contract mismatch → retire in S02 by proving each track has a documented, aggregate-safe export surface suitable for downstream consumption
- Agent planning drift → retire in S03 by proving the feature-plan / sprint / phase structure maps directly to real repo areas and milestone intent
- Story fragmentation → retire in S04 by proving the trust-marketplace narrative and intern-explainer workflow reflect the actual track work instead of marketing abstractions
- Integration risk across all surfaces → retire in S05 by proving the outputs, export contract, planning structure, and narrative layer agree in one local verification pass

## Verification Classes

- Contract verification: file existence checks, artifact completeness checks, markdown/doc review, export manifest checks, and plan-structure checks
- Integration verification: local exercise of the current CLI pipeline and downstream handoff surfaces from `outputs/` into the planned export contract
- Operational verification: local rerun/verification flow only; no cloud deployment or service lifecycle work in this milestone
- UAT / human verification: none required for milestone completion; later presentation quality can be judged in M004

## Milestone Definition of Done

This milestone is complete only when all are true:

- all slice deliverables are complete
- the five-track EDA layer is actually verified against live repo outputs rather than assumed from code presence
- the export contract exists and is grounded in aggregate-safe artifacts the later website and report can consume
- the feature-plan / sprint / phase structure exists and is detailed enough for downstream implementation agents
- the trust-marketplace story and intern-explainer workflow are documented in terms that match the actual work
- final integrated handoff verification passes and M002 can start without first rebuilding context

## Requirement Coverage

- Covers: R001, R002, R003, R004, R013
- Partially covers: R011, R012
- Leaves for later: R005, R006, R007, R008, R009, R010, R020, R021, R022
- Orphan risks: none

## Slices

- [x] **S01: All-track EDA artifact census and gap closure** `risk:high` `depends:[]`
  > After this: the team can point to verified final EDA summary artifacts for all five tracks and see exactly what was repaired versus already present.

- [x] **S02: Export contract and evidence packaging** `risk:high` `depends:[S01]`
  > After this: each track has an aggregate-safe export surface that later modeling, reporting, and the local website can consume.

- [x] **S03: Agent-ready planning architecture** `risk:medium` `depends:[S01]`
  > After this: distinct feature-plan folders, sprint subfolders, and phase docs exist as the execution surface for downstream implementation agents.

- [x] **S04: Trust narrative and intern explainer workflow** `risk:medium` `depends:[S02,S03]`
  > After this: the repo explains the work as a trust-marketplace system and formalizes when to invoke an agent to explain the process to interns.

- [x] **S05: Integrated local handoff verification** `risk:medium` `depends:[S02,S03,S04]`
  > After this: the evidence layer, export contract, planning structure, and narrative layer are verified together and ready to hand off into baseline modeling.

## Boundary Map

### S01 → S02

Produces:
- Verified final summary markdowns for Tracks A–E under `outputs/tables/track_*_eda_summary.md`
- A concrete completeness matrix listing which track artifacts existed, which were missing, and which were repaired
- A verified command/file checklist for the current brownfield EDA entrypoints

Consumes:
- nothing (first slice)

### S01 → S03

Produces:
- Real repo-grounded understanding of which code paths, outputs, and track rules later plans must reference
- Confirmed current-state constraints from `scripts/run_pipeline.py`, `scripts/pipeline_dispatcher.py`, `src/eda/track_*`, `data/curated/`, and `outputs/`

Consumes:
- nothing (first slice)

### S02 → S04

Produces:
- Track-level export contracts for JSON/CSV/PNG/MD artifacts
- A packaging convention the future local-hosted website and report flow can reference
- Governance-safe rules for what may and may not appear in shared exports

Consumes from S01:
- Verified final EDA summaries and completeness findings

### S03 → S04

Produces:
- Distinct feature-plan folder convention
- Sprint subfolder convention for each feature plan
- Phase-doc convention inside each sprint so later agents inherit a predictable execution structure

Consumes from S01:
- Real repo-grounded understanding of what must be planned

### S02 → S05

Produces:
- Stable export surfaces and packaging rules ready for verification

Consumes from S01:
- Verified track outputs and completeness status

### S03 → S05

Produces:
- Stable planning surfaces ready for verification

Consumes from S01:
- Repo-grounded planning constraints

### S04 → S05

Produces:
- Trust-marketplace narrative mapping across Tracks A–E
- Documented intern-explainer invocation workflow and purpose

Consumes from S02:
- Export surfaces and governance-safe evidence rules

Consumes from S03:
- Feature-plan / sprint / phase planning structure
