# M005-i0a235 — Research

**Date:** 2026-03-24

## Summary

M005 should start with a **photo-ingestion and contract integrity slice**, not with model training.

In this worktree, the current pipeline is strong for shared ingestion/curation + EDA Tracks A–E, but there is **no implemented photo entity path** and no multimodal runtime lane yet. The first proof should therefore be:

1. can we ingest and align photo assets/metadata safely and reproducibly,
2. can we run one narrow multimodal baseline with explicit compute accounting,
3. can we make a stop/expand decision from that evidence.

Given current constraints, the safest first experiment is a **snapshot-framed multimodal pass** (Track B-aligned framing) rather than a strict temporal as-of task that would depend on unavailable photo timestamps.

---

## Key Findings (Codebase Reality)

### 1) Photo/image is not wired into current ingestion or curated contracts

Evidence:
- `configs/base.yaml` defines only 5 entities (`business`, `review`, `user`, `tip`, `checkin`) and one tar path (`data/raw/Yelp-JSON/Yelp JSON/yelp_dataset.tar`).
- `src/ingest/load_yelp_json.py` `SCHEMAS` covers those same 5 entities only.
- `src/ingest/validate_json_structure.py` validates those same 5 entities only.
- `src/curate/build_review_fact.py` exports curated surfaces for non-photo entities only.
- `src/curate/build_sample.py` sample manifest/files also exclude photo.

Implication: a real multimodal experiment cannot be “just modeling work”; it needs a new upstream ingestion/curation surface first.

### 2) Prior planning already warned about photo path mismatch and separation

Evidence in planning docs:
- `CoWork Planning/yelp_project/09_Resolution_TrackA_TrackB_Implementation_Plan.md` states photo is out-of-scope for A/B shared ingestion and must be separate if added later.
- `CoWork Planning/yelp_project/08_PM_Adversarial_Review_Implementation_Plan.md` documents `Dataset(Raw)/Yelp Photos/yelp_photos.tar` as separate from main JSON tar.
- `README.md` repeats optional photo archive as separate asset.

Implication: the natural design is a **second extraction branch** for photos, not extending current shared A/B contracts in-place.

### 3) Orchestration has no multimodal approach slot

Evidence:
- `scripts/pipeline_dispatcher.py` approaches are `shared`, `track_a`, `track_b`, `track_c`, `track_d`, `track_e`.
- `scripts/run_pipeline.py` UI/aliases mirror the same approach set.

Implication: M005 needs either:
- standalone module entrypoints (simplest first), or
- explicit new dispatcher approach for reproducibility.

### 4) Compute support exists, but only for tabular/EDA acceleration

Evidence:
- `docs/gpu_acceleration.md` and `requirements-gpu.txt` support cudf-polars + optional Sirius, mainly for Polars/DuckDB workloads.
- `requirements.txt` has no `torch`, `transformers`, `pillow`, etc.

Implication: M005 introduces a new compute/runtime stack; local GPU-first is feasible, but dependency/bootstrap must be explicit and isolated.

### 5) Governance constraints are strong and directly affect multimodal design

Evidence:
- Root/project constraints and `R013`/`R031` require aggregate-safe internal outputs.
- Track E helpers (`src/eda/track_e/common.py`) already enforce no raw text/demographic inference style guardrails.

Implication: multimodal outputs should avoid raw image redistribution in deliverables; use aggregate metrics/manifests only.

### 6) Surprise: worktree state is EDA-centric despite milestone history referencing broader modeled/showcase surfaces

Observed in this worktree:
- no `src/modeling/` directory,
- no `data/` materialized by default.

Implication: roadmap should include an early “state reality” gate for M005 assumptions to avoid planning against non-present artifacts.

---

## What Should Be Proven First

1. **Photo intake viability**
   - Separate archive extraction works.
   - Photo metadata and image files can be linked reliably by `photo_id`/`business_id`.
   - Missing/corrupt image rate is measured.

2. **Narrow multimodal baseline is runnable**
   - One frozen, pretrained image encoder baseline (no heavy fine-tune).
   - One bounded subset size and deterministic seed.

3. **Value-vs-cost evidence is explicit**
   - Delta vs non-image baseline on one metric family.
   - GPU hours/wall-clock/VRAM/peak RAM captured.
   - Stop/expand decision rendered from thresholds.

---

## Recommended First Experiment Framing

### Why snapshot-first is safer than temporal-first

Photo records commonly lack robust event-time semantics needed for strict as-of leakage controls. Given existing repo emphasis on no-future-leakage and honest contracts, first experiment should avoid pretending temporal validity where timestamps are ambiguous.

### Suggested first lane

- **Primary recommendation:** Track B-aligned snapshot setting with business-level photo embeddings fused with existing non-image features.
- **Alternative (higher risk):** Track D1 business cold-start fusion if photo timestamp semantics are made explicit and acceptable.

Reasoning: snapshot framing minimizes leakage ambiguity and lets M005 answer R020/R021 quickly.

---

## Existing Patterns to Reuse

- **Config-driven paths/inheritance:** `src/common/config.py` + `configs/*.yaml`.
- **Central DuckDB connection policy:** `src/common/db.py`.
- **Artifact contract style:** dispatcher `required_outputs` + stage output determinism.
- **Bounded computation pattern:** Track D `evaluation.entity_cap_per_group` style cap.
- **Sample-first feasibility path:** `src/curate/build_sample.py` for narrow-scope iteration.

---

## Boundary Contracts That Matter

1. **Photo Intake Contract (new)**
   - Input: separate photo tar path.
   - Output: canonical photo metadata parquet + resolved image-path manifest + integrity report.

2. **Fusion Dataset Contract (new)**
   - Join key(s): `business_id` required, `photo_id` optional per-photo rows.
   - Explicit handling for businesses with zero photos.
   - Deterministic subset/cap fields (`max_businesses`, `max_photos_per_business`, seed).

3. **Experiment Evidence Contract (new)**
   - Baseline metric(s), multimodal metric(s), delta.
   - Compute accounting fields (`wall_clock_sec`, `gpu_name`, `peak_vram_mb`, `peak_ram_mb`).
   - Decision field: `expand_recommended` boolean + rationale text.

4. **Governance Contract (continuity)**
   - No raw review text in outputs.
   - No photo/image redistribution in showcase/report exports.
   - Aggregate-safe summaries only.

---

## Known Failure Modes That Should Shape Slice Ordering

1. **Scope balloon:** jumping to multi-model benchmarking before proving one baseline.
2. **Data-path fragility:** image files missing/unreadable, broken joins.
3. **Leakage ambiguity:** using undated photos in temporal claims.
4. **Compute overrun:** introducing training-heavy models too early.
5. **Narrative drift:** running a disconnected CV project not tied to trust-marketplace questions.

---

## Requirement Analysis (M005 + Active Continuity)

### Table stakes for M005

- **R020 (deferred):** one real narrow multimodal experiment.
- **R021 (deferred):** expansion only if value beats compute burden.

### Active continuity requirements that still matter

- **R022 (active):** local-first compute; overflow only when evidence-based triggers are hit.
- **R013/R031 constraints:** internal + aggregate-safe outputs; avoid raw image/text publication.

### Likely omissions for roadmap discussion (candidate requirements)

1. **Candidate requirement:** explicit photo intake integrity contract.
2. **Candidate requirement:** mandatory compute-accounting artifact for M005 experiment.
3. **Candidate requirement:** explicit leakage posture for photo time semantics (snapshot-only vs temporal-allowed).
4. **Candidate requirement:** hard cap on experiment scope for first pass.

---

## Skill Discovery (suggest)

No currently installed skill is directly specialized for multimodal CV pipelines in this environment.

Promising external skills (not installed):

- **PyTorch**
  - `npx skills add pytorch/pytorch@skill-writer` (highest installs)
- **Hugging Face Transformers**
  - `npx skills add mindrally/skills@transformers-huggingface`
- **DuckDB**
  - `npx skills add silvainfm/claude-skills@duckdb`
- **Polars**
  - `npx skills add davila7/claude-code-templates@polars`
- **scikit-learn**
  - `npx skills add davila7/claude-code-templates@scikit-learn`

---

## Targeted Library Notes (Context7)

Using Hugging Face Transformers docs (`/llmstxt/huggingface_co_transformers_v5_2_0_llms_txt`):

- `CLIPModel` + `AutoProcessor` supports immediate training-free image/text embedding and similarity baselines.
- `get_image_features`/forward-pass APIs support extracting image embeddings for fusion experiments.

Why this matters: M005 can run a credible first experiment without fine-tuning, reducing compute risk while still being “true multimodal.”

---

## Suggested Slice Boundaries for Roadmap Planner

1. **S1 — Photo intake + integrity contract**
   - Separate archive extraction, metadata normalization, image-path validation.

2. **S2 — Fusion-ready dataset builder (bounded)**
   - Join photo features to one existing track framing with deterministic caps.

3. **S3 — First multimodal baseline run + compute ledger**
   - Pretrained frozen encoder baseline; compare against non-image baseline.

4. **S4 — Expand-or-stop decision gate**
   - Apply thresholded decision criteria from S3 outputs.

5. **S5 — Conditional overflow compute enablement**
   - Only if S3 fails local viability and value potential remains plausible.

---

## Direct Answers to Strategic Questions

- **What should be proven first?**
  - That photo intake/alignment is reliable and one bounded multimodal baseline can run end-to-end.

- **What existing patterns should be reused?**
  - Config-driven contracts, deterministic artifact outputs, bounded computation caps, and governance-first validation.

- **What boundary contracts matter?**
  - Photo intake manifest, fusion dataset schema, compute-accounting artifact, and explicit leakage posture.

- **What constraints does the existing codebase impose?**
  - No current photo ingestion path, no multimodal dispatcher approach, no deep-learning dependencies, strict aggregate-safe constraints.

- **Known failure modes shaping order?**
  - Scope balloon, broken photo joins, leakage ambiguity, compute blow-up, disconnected side-project drift.

- **Which findings should become candidate requirements vs advisory only?**
  - Candidate requirements: photo integrity contract, compute ledger, leakage posture, first-pass scope cap.
  - Advisory only: specific model family choice (CLIP variant), which can stay implementation-flexible.
