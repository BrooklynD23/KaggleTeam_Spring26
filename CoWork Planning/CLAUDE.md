---
id: cowork_planning
title: CoWork Planning — Original Agent Task Context
version: "2026-03-18"
scope: cowork
tags: [planning, prd, semester-project, track-definitions, inception]

cross_dependencies:
  reads:
    - CoWork Planning/yelp_project/01_PRD_Yelp_Open_Dataset.md
    - CoWork Planning/yelp_project/07_Implementation_Plan_Ingestion_TrackA_TrackB.md
  writes:
    - CoWork Planning/yelp_project/01_PRD_Yelp_Open_Dataset.md
    - CoWork Planning/yelp_project/02_EDA_Pipeline_Track_A_Future_Ratings.md
    - CoWork Planning/yelp_project/03_EDA_Pipeline_Track_B_Usefulness_Ranking.md
    - CoWork Planning/yelp_project/04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md
    - CoWork Planning/yelp_project/05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md
    - CoWork Planning/yelp_project/06_EDA_Pipeline_Track_E_Bias_Disparity.md
  siblings: [root]

toc:
  - section: "Context for this task"
    anchor: "#context-for-this-task"
  - section: "Required outputs"
    anchor: "#required-outputs"
  - section: "Key constraints"
    anchor: "#key-constraints"
  - section: "Grounding source"
    anchor: "#grounding-source"
  - section: "Tone"
    anchor: "#tone"
  - section: "Structure expectations"
    anchor: "#structure-expectations"
  - section: "Important execution note"
    anchor: "#important-execution-note"
---

# Context for this task

The user wants a **semester-scale PRD** for the **Yelp Open Dataset** plus **one markdown file per approach** for these 5 framing questions:

1. Future star rating prediction under **strict time-split evaluation**
2. Review **usefulness-vote** drivers and ranking
3. **Sentiment/topic drift** over time by city/neighborhood
4. **Cold-start recommendation** for new businesses/users
5. **Bias/disparity** in ratings and recommendations

## Required outputs
Create actual files, not just chat text:

- `01_PRD_Yelp_Open_Dataset.md`
- `02_EDA_Pipeline_Track_A_Future_Ratings.md`
- `03_EDA_Pipeline_Track_B_Usefulness_Ranking.md`
- `04_EDA_Pipeline_Track_C_Sentiment_Topic_Drift.md`
- `05_EDA_Pipeline_Track_D_Cold_Start_Recommender.md`
- `06_EDA_Pipeline_Track_E_Bias_Disparity.md`
- optional: `README.md` and zip bundle

## Key constraints
- The 5 track files are for **EDA only**, not full modeling specs
- Pipelines must be **CLI-first**, reproducible, and clean
- Use **repeatable staged workflows**, not notebook-centric exploration
- Emphasize **temporal leakage prevention** and **as-of feature logic**
- Keep outputs **aggregate-safe**; avoid recommending public raw review display

## Grounding source
An uploaded PDF about semester-scale data science datasets includes Yelp guidance. Use it to shape the documents:
- Yelp is a multi-entity JSON dataset
- Good for rating prediction, helpfulness ranking, recommendation, geospatial and temporal NLP
- Requires careful leakage control
- **Strict time-based splits** are important
- Prefer aggregate/privacy-safe outputs

## Tone
Write like a strong capstone / advanced data science project spec:
- practical
- structured
- implementation-oriented
- not overly academic
- markdown only

## Structure expectations

### PRD
Should include:
- executive summary
- problem statement
- scope / non-goals
- stakeholders
- dataset/entity overview
- track-by-track goals
- evaluation philosophy
- risks / mitigations
- semester roadmap
- success criteria
- suggested repo / pipeline architecture

### Each EDA pipeline file
Should include:
- framing question
- EDA objective
- required entities
- curated / derived tables
- CLI pipeline stages
- example commands
- outputs
- validation checks
- leakage checks
- visual deliverables
- exit criteria
- handoff to modeling

## Important execution note
A previous agent failed by claiming files existed before actually generating them.

Do not do that.

Only provide links after the files are truly created.