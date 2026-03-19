# Notebook EDA

Jupyter notebooks for running EDA on a stratified sample of the Yelp dataset. Run on heavy hardware, commit executed notebooks (with embedded figures), and review on light laptops without re-running.

## Prerequisites

1. Run the shared pipeline once: `python scripts/run_pipeline.py --approach shared`
2. Build the sample: `python -m src.curate.build_sample --config configs/base.yaml`
3. Install Jupyter: `pip install jupyter ipykernel`

## Run Order

- **Track A** must run first (Track D depends on its Stage 5 split artifact)
- **Track B, C, E** can run in any order
- **Track D** requires Track A to have been run first (guard cell will stop with a clear instruction if not)

## Heavy vs Light Workflow

1. **Heavy hardware:** Run all cells in each notebook. Figures and tables are embedded in the `.ipynb` JSON.
2. **Commit:** `notebooks/*.ipynb`, `configs/*_sample.yaml`, `data/sample/*`
3. **Light laptops:** Pull the repo and open the notebooks. No execution needed — outputs are already embedded for review.

## Sample vs Full Dataset

- Notebooks use `configs/track_*_sample.yaml`, which points `curated_dir` to `data/sample`
- For full-dataset EDA, run the pipeline via `python scripts/run_pipeline.py --approach track_a` etc. (uses `data/curated`)
- The sample is ~20K reviews stratified by year and stars; suitable for quick iteration and Git commit
