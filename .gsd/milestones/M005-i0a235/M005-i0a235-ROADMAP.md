# M005-i0a235: M005-i0a235: Future multimodal extensions — Context

**Vision:** Deliver one real, bounded multimodal experiment that fuses Yelp photo information with existing non-image surfaces, measures value vs compute honestly, and yields a clear expand-or-stop decision without derailing the core semester path.

## Success Criteria

- A reproducible photo intake path exists as a separate branch from shared JSON ingestion, with integrity metrics (linkability, missing/corrupt rates) and deterministic artifacts.
- A bounded fusion dataset can be built from existing curated surfaces plus photo-derived features in a snapshot-safe framing, including explicit handling of zero-photo businesses.
- One true multimodal baseline run (frozen pretrained image encoder + non-image features) is completed and compared against a non-image baseline on defined metrics.
- Compute/resource accounting (wall-clock, GPU/CPU memory signals, hardware identity, run scope) is captured in a machine-readable ledger tied to experiment outputs.
- An explicit expand-or-stop decision artifact is produced with thresholded rationale; overflow compute (Colab/HPC) is only activated when local evidence-based triggers are met.

## Slices

- [ ] **S01: Photo intake and integrity contract (separate branch)** `risk:high` `depends:[]`
  > After this: After this slice, the team can run a canonical photo-intake command and inspect deterministic artifacts that show how many photos were discovered, linked, missing, unreadable, and usable for downstream fusion.

- [ ] **S02: Bounded fusion dataset for snapshot-safe multimodal framing** `risk:high` `depends:[S01]`
  > After this: After this slice, stakeholders can inspect a fusion dataset artifact that joins non-image features with photo-derived embeddings/aggregates on a bounded scope, including explicit coverage for businesses with zero photos.

- [ ] **S03: First multimodal baseline run with compute ledger** `risk:high` `depends:[S02]`
  > After this: After this slice, the team can open a machine-readable experiment packet showing non-image baseline metrics vs multimodal metrics plus runtime and memory accounting from a real bounded run.

- [ ] **S04: Expand-or-stop decision gate with conditional overflow compute triggers** `risk:medium` `depends:[S03]`
  > After this: After this slice, a stakeholder can read a single decision artifact that states expand vs stop, the threshold checks used, and whether overflow compute is authorized or denied for next steps.

## Boundary Map

- Upstream dependencies: existing curated/tabular surfaces and baseline modeling outputs from prior milestones; optional separate Yelp photo archive path.
- New contracts introduced in M005:
  - Photo Intake Contract: photo metadata parquet + image path manifest + integrity report.
  - Fusion Dataset Contract: bounded snapshot-safe join keyed by `business_id` with deterministic caps/seeds and zero-photo handling.
  - Experiment Evidence Contract: baseline/multimodal metrics, delta, compute ledger, and decision field.
- Runtime boundaries:
  - Local GPU-first execution path (default).
  - Conditional overflow path (Colab/HPC) activated only by explicit trigger thresholds.
- Governance boundaries:
  - No raw review text in outputs.
  - No raw image redistribution in published deliverables.
  - Aggregate-safe/internal-only reporting surfaces.
