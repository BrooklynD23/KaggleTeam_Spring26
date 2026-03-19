# GPU Acceleration (Experimental)

This document describes optional GPU acceleration paths for the pipeline.
These are **not required** for the main pipeline to work. The official
pipeline is CPU-only and runs on Windows natively.

## Pipeline Integration

When you run the pipeline via `python scripts/run_pipeline.py`, the launcher:

1. **Checks** whether GPU packages (cudf-cu12, cudf-polars-cu12) are installed
2. **Prompts** you to install them if not: "Install optional GPU packages for faster pipeline? [y/N]"
3. **Uses GPU** automatically when available — stages that use `src.common.parquet_io` will run Polars `.collect(engine="gpu")` to cut down on time and resources

No manual configuration is needed. If you decline or install fails, the pipeline runs on CPU as before.

## Prerequisites

All GPU options require:
- NVIDIA GPU with CUDA support
- WSL2 on Windows (RAPIDS and Sirius are Linux-native)
- CUDA Toolkit 12.x installed in the WSL2 environment

**Note:** On Windows native (without WSL2), `pip install -r requirements-gpu.txt` will fail because cudf provides no Windows wheels. The pipeline will continue with CPU. Use WSL2 for GPU acceleration on Windows.

## Option 1: cudf-polars (Recommended First Experiment)

`cudf-polars` is a drop-in GPU backend for Polars that accelerates lazy
frame execution on NVIDIA GPUs. Since the pipeline already uses Polars
(via `src/common/parquet_io.py`), this layers on top with minimal changes.

### Setup (WSL2)

```bash
pip install -r requirements-gpu.txt
# or manually:
pip install cudf-cu12 cudf-polars-cu12
```

Alternatively, run the pipeline and answer **y** when prompted to install.

### Usage

The pipeline launcher sets `YELP_POLARS_ENGINE=gpu` when GPU packages are
available. `src.common.parquet_io.collect_frame()` and
`read_parquet_pandas()` then use `engine="gpu"` automatically.

For manual usage:

```python
import polars as pl

# Enable GPU execution for a lazy frame
lf = pl.scan_parquet("data/curated/review_fact.parquet")
result = lf.group_by("review_year").agg(pl.len()).collect(engine="gpu")
```

No changes to existing code are required beyond passing `engine="gpu"`
to `.collect()` calls. If no GPU is available, Polars falls back to CPU
automatically.

### Where to Apply

Any stage that uses `src.common.parquet_io.scan_parquet()` can benefit.
The highest-impact targets are stages with large aggregations or groupby
operations on `review_fact.parquet` (~7M rows).

## Option 2: Sirius (DuckDB GPU Extension)

Sirius is a DuckDB extension that offloads SQL operators (JOINs,
aggregations, projections) to the GPU via NVIDIA RAPIDS cuDF.

### Setup (WSL2)

```bash
# Inside a DuckDB session or Python:
import duckdb
con = duckdb.connect()
con.execute("INSTALL sirius")
con.execute("LOAD sirius")
```

Sirius requires the NVIDIA CUDA-X libraries and RAPIDS Memory Manager.
See https://github.com/sirius-db/sirius for build instructions.

### Where to Apply

The single best candidate is the heavy 3-table JOIN in
`src/curate/build_review_fact.py` (`REVIEW_FACT_SQL`). This joins
review + business + user tables and is the most expensive SQL operation
in the pipeline.

**Note:** Track D Stage 7 (`evaluation_cohorts.py`) was rewritten to use
bounded pandas-based construction instead of spill-heavy DuckDB joins.
It is no longer a DuckDB bottleneck and does not need GPU acceleration.

To test, add `LOAD sirius;` after opening the DuckDB connection
in `build_review_fact.py`.

### Caveats

- Sirius is early-stage (released mid-2025, ~900 GitHub stars)
- Documentation is sparse; build-from-source may be required
- Only tested on Linux; WSL2 is the Windows path

## Option 3: FAISS (Vector Similarity Search)

The FAISS DuckDB community extension provides GPU-accelerated nearest-
neighbor search. This is **not relevant** for the current EDA pipeline.

It becomes relevant when Track D moves from EDA to model building and
needs embedding-based recommendation (finding similar businesses/users).

### Setup

```sql
INSTALL faiss FROM community;
LOAD faiss;
-- Move index to GPU (Linux + CUDA only)
CALL FAISS_TO_GPU('index_name', 0);
```

## Decision Framework

| Question | Answer | Action |
|----------|--------|--------|
| Need faster EDA now? | Yes | Use cudf-polars |
| Need faster curation JOIN? | Yes | Try Sirius on build_review_fact |
| Building a recommender? | Yes | Use FAISS for nearest-neighbor |
| No NVIDIA GPU? | Yes | Stick with CPU Polars + DuckDB tuning |

## Benchmarking

Before promoting any GPU path to the main pipeline:

1. Run the full pipeline with timing telemetry (`pipeline_dispatcher.py`
   now logs per-stage wall-clock time)
2. Compare GPU vs CPU times for the same stages
3. Verify output equivalence (row counts, null rates, key aggregates)
4. Document setup steps and reproduce on a clean environment
