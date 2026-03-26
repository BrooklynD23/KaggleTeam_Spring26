---
estimated_steps: 4
estimated_files: 5
skills_used:
  - coding-standards
  - security-review
  - test
  - verification-loop
---

# T02: Enforce governance-safe packaging rules and publish the export contract

**Slice:** S02 — Export contract and evidence packaging
**Milestone:** M001-4q3lxl

## Description

Harden the export bundle so it is safe to hand to downstream consumers. This task turns `R013` into executable behavior by constraining what the packager may emit, documenting the internal-only / aggregate-safe boundary in a generated contract, and extending tests so convenience copies of raw artifacts or logs fail immediately.

## Steps

1. Extend `scripts/package_eda_exports.py` with explicit allowlist/exclusion logic so only S01 evidence markdown plus synthesized export metadata can enter `outputs/exports/eda/`; do not copy `.parquet`, `.ndjson`, or raw `.log` files into the bundle.
2. Generate `outputs/exports/eda/EXPORT_CONTRACT.md` from the packager, documenting bundle layout, per-format consumer expectations, `existing` / `missing` semantics, Track D's blocker rule, and the no-raw-review-text / internal-only governance boundary.
3. If the bundle needs to preserve any insight from `outputs/logs/track_e_s9_validity_scan.log`, summarize it into metadata instead of copying the log file itself.
4. Expand `tests/test_package_eda_exports.py` so forbidden artifact types, missing-governance language, or status-semantic drift fail loudly.

## Must-Haves

- [ ] The packager enforces an allowlist/exclusion boundary in code instead of relying on operator discipline.
- [ ] `EXPORT_CONTRACT.md` clearly states that the bundle is aggregate-safe, internal-use oriented, and free of raw review text / raw storage copies.
- [ ] Tests fail if `.parquet`, `.ndjson`, or copied `.log` files appear under `outputs/exports/eda/`, or if missing upstream artifacts stop being labeled `missing`.

## Verification

- `python -m pytest tests/test_package_eda_exports.py`
- `python scripts/package_eda_exports.py && python - <<'PY'
from pathlib import Path
root = Path('outputs/exports/eda')
forbidden = [p.as_posix() for p in root.rglob('*') if p.is_file() and p.suffix in {'.parquet', '.ndjson', '.log'}]
assert not forbidden, forbidden
contract = (root / 'EXPORT_CONTRACT.md').read_text(encoding='utf-8')
assert 'aggregate-safe' in contract
assert 'internal' in contract
assert 'raw review text' in contract
PY`

## Inputs

- `scripts/package_eda_exports.py` — bundle generator created in T01
- `tests/test_package_eda_exports.py` — contract test file to extend with governance assertions
- `outputs/tables/eda_artifact_census.csv` — source of truth for honest `missing` statuses
- `outputs/tables/track_d_s9_eda_summary.md` — blocker language to preserve without overstating completeness
- `outputs/logs/track_e_s9_validity_scan.log` — example log surface that must be summarized or excluded, not blindly copied

## Expected Output

- `scripts/package_eda_exports.py` — updated with allowlisting, exclusion rules, and contract generation
- `tests/test_package_eda_exports.py` — expanded with governance and forbidden-artifact assertions
- `outputs/exports/eda/EXPORT_CONTRACT.md` — generated contract for downstream consumers
- `outputs/exports/eda/manifest.json` — root manifest reflecting safe emitted outputs only
- `outputs/exports/eda/tracks/track_d/artifacts.csv` — representative per-track artifact table still showing missing/blocker semantics

## Observability Impact

- Runtime signals now include explicit governance metadata in the root and per-track manifests: safe emitted file counts, forbidden-source exclusions, and any Track E validity-log summary carried forward without copying the raw log.
- Future agents can inspect `outputs/exports/eda/manifest.json`, `outputs/exports/eda/EXPORT_CONTRACT.md`, and `outputs/exports/eda/tracks/*/manifest.json` to confirm the bundle remained aggregate-safe, internal-only, and honest about `existing` / `missing` artifact status.
- Failure states become visible as deterministic test failures and path-specific bundle assertions when a forbidden `.parquet`, `.ndjson`, or `.log` file enters the export, or when governance language/status semantics drift out of the generated contract and manifests.
