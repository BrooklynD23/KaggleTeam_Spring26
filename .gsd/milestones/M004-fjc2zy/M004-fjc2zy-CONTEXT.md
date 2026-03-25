---
depends_on: [M001-4q3lxl, M002-c1uww6, M003-rdpeu4]
---

# M004-fjc2zy: Local showcase, report, and presentation system — Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

## Project Description

This milestone turns the analytical and modeling work into the final internal academic showcase. It includes:

- a local-hosted Next.js + Motion website
- the final report
- the final presentation deck

The site should be **hybrid**: executive story first, track drill-downs second. It is not a public product and it should not become a live analytics backend. It should present the work in a **business oriented approach** while staying grounded in evidence.

## Why This Milestone

The user explicitly said the project will fail if the modeling is weak or the story is weak. This milestone is where the story gets assembled into a coherent artifact for the team and department showcase.

## User-Visible Outcome

### When this milestone is complete, the user can:

- run a local-hosted website that presents the semester work through the trust-marketplace narrative
- deliver a final report and deck that connect the tracks into one business-oriented system story

### Entry point / environment

- Entry point: local Next.js app plus final report/deck artifacts
- Environment: local dev / browser
- Live dependencies involved: none required beyond local exported artifacts

## Completion Class

- Contract complete means: the site, report, and deck exist with real content tied to actual project evidence
- Integration complete means: the site reads exported JSON/CSV/PNG/MD artifacts from the repo’s packaging flow rather than depending on live analytical queries
- Operational complete means: the showcase runs locally without AWS or public hosting infrastructure

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- the local-hosted site runs and presents the project as a trust-marketplace story
- the report and deck reflect the same evidence, same track framing, and same conclusions
- the artifact flow from repo outputs to showcase surfaces is robust enough for real demo use

## Risks and Unknowns

- There is no website setup yet in the repo
- Motion templates for the landing page are intentionally delayed until the website sprint, so the mock-up must be planned first
- The final narrative can still fragment if the earlier milestones do not package evidence consistently

## Existing Codebase / Prior Art

- No existing Next.js scaffold is present in the repo today
- M001 export contract is expected to provide the website’s data inputs
- M001 trust-story work is expected to provide the narrative skeleton for the site, report, and deck

## Relevant Requirements

- R011 — Produce a robust local-hosted internal academic website using exported JSON/CSV/PNG artifacts
- R012 — Produce a final report and presentation deck anchored in the “trust marketplace” narrative
- R013 — Preserve governance-safe outputs for internal academic team and department showcase use only

## Scope

### In Scope

- local website
- final report
- final presentation deck
- hybrid executive-story + track drill-down information architecture

### Out of Scope / Non-Goals

- public cloud hosting
- live backend analytics product behavior
- public-facing distribution

## Technical Constraints

- The site must be local-hosted
- The site should consume exported artifacts rather than query analytical storage live
- The mock-up should be planned before Motion landing-page templates are pulled in

## Integration Points

- exported JSON/CSV/PNG/MD artifacts from M001–M003
- local browser runtime
- final written and presentation deliverables

## Open Questions

- What exact information architecture best serves the hybrid executive-story + drill-down requirement?
- Which visualizations are canonical enough to feature on the landing flow versus drill-down track pages?
- How much interactivity is necessary to strengthen the story without obscuring the evidence?
