---
depends_on: [M002-c1uww6]
---

# M005-i0a235: Future multimodal extensions — Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

## Project Description

This milestone is the future-works lane for true multimodal photo/image exploration. The user wants to explore this area, but not at the expense of the core semester path. The intended sequence is:

1. finish the EDA and core baseline modeling path
2. run one narrow true multimodal experiment
3. only expand if the first experiment clearly justifies the compute cost and complexity

## Why This Milestone

The Yelp dataset includes photo metadata and separate photo assets, and the team has enough compute access to explore multimodal work if the core path is already secure. This milestone preserves that ambition without pretending it belongs on the critical path.

## User-Visible Outcome

### When this milestone is complete, the user can:

- point to one true multimodal experiment that combines non-image signals with image/photo information
- make an evidence-based call on whether deeper multimodal work is worth the overhead

### Entry point / environment

- Entry point: modeling/experiment workflows defined later
- Environment: local GPU first, then Colab Pro or HPC only if the experiment justifies it
- Live dependencies involved: optional photo archive path, local GPU, optional backup compute

## Completion Class

- Contract complete means: one narrow multimodal experiment exists with explicit compute accounting and evidence of value or lack of value
- Integration complete means: the multimodal lane consumes the existing core data/modeling surfaces instead of becoming a parallel disconnected project
- Operational complete means: resource overhead is understood well enough to decide whether to continue

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- one real multimodal experiment ran on a justified scope
- the compute/resource overhead was measured honestly
- the result led to a clear expand-or-stop decision

## Risks and Unknowns

- Multimodal scope can balloon quickly
- Photo ingestion and feature alignment may require repo changes not yet planned in detail
- The first experiment may not justify the cost, which is an acceptable outcome if measured honestly

## Existing Codebase / Prior Art

- The current PRD acknowledges photo metadata but excludes deep image modeling from the current core scope
- The raw photo archive path has been noted in planning documents as separate from the main JSON archive
- No current multimodal training path exists in the repo

## Relevant Requirements

- R020 — Run a first true multimodal photo/image experiment on a narrow, justified scope
- R021 — Expand multimodal work beyond the first experiment if it shows clear value relative to compute cost
- R022 — Enable Colab Pro and/or HPC overflow as a conditional fallback if local baseline quality or runtime is insufficient

## Scope

### In Scope

- one narrow multimodal experiment
- resource-overhead analysis
- expand-or-stop decision criteria

### Out of Scope / Non-Goals

- treating multimodal work as guaranteed semester-critical scope
- broad image-model benchmarking without a clear framing-question tie-in

## Technical Constraints

- start narrow
- preserve the core semester path first
- justify any heavier compute escalation with evidence

## Integration Points

- upstream modeling outputs from earlier milestones
- optional photo assets and metadata
- local GPU, Colab Pro, and HPC as compute options

## Open Questions

- Which track should carry the first true multimodal experiment?
- What resource budget is acceptable before the experiment is judged too expensive for the gain?
- Does the first experiment justify further expansion or not?
