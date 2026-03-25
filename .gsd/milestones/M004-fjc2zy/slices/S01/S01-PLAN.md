# S01: Intake-locked showcase shell with visible readiness and blocked states

**Goal:** Ship the first runnable local showcase shell that is intake-locked to a canonical manifest, so missing upstream evidence is surfaced as explicit blocked diagnostics before any executive-story polish.
**Demo:** From a fresh worktree, run the intake command and start the app; the homepage renders a readiness summary with ready/missing counts and a blocked list tied to concrete artifact paths (instead of silent placeholders).

## Must-Haves

- S01 directly advances **R011** by introducing a local-hosted Next.js showcase shell that can be run with one local command path.
- S01 supports **R013** by making governance/internal-only markers visible in intake diagnostics and homepage status copy.
- S01 supports **R022** continuity by checking for M003 closeout evidence surfaces and showing explicit blocked reasons when they are absent.
- Intake truth is machine-readable and deterministic via one canonical generated bundle: `outputs/showcase/intake/manifest.json` + `outputs/showcase/intake/validation_report.json`.
- Homepage readiness and blocked states are driven by that generated intake bundle, not hardcoded UI mocks.

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: no

## Verification

- `python -m pytest tests/test_showcase_intake_contract.py -q`
- `python -m pytest tests/test_showcase_intake_contract.py -q -k missing`
- `python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake && test -f outputs/showcase/intake/manifest.json && test -f outputs/showcase/intake/validation_report.json`
- `npm --prefix showcase run test -- --run`
- `python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000`
- `npm --prefix showcase run build`

## Observability / Diagnostics

- Runtime signals: intake `status`, per-surface `ready|missing` states, blocked reason codes, and generated timestamp in `manifest.json` / `validation_report.json`.
- Inspection surfaces: `python scripts/build_showcase_intake.py ...`, `outputs/showcase/intake/*.json`, homepage readiness panel, and `python scripts/showcase_smoke_check.py ...` output.
- Failure visibility: missing required paths are reported with explicit artifact path + requirement key + reason; shell load failures surface a visible "intake unavailable" state rather than blank UI.
- Redaction constraints: diagnostics remain aggregate-safe/internal-only and must not include raw review text payloads.

## Integration Closure

- Upstream surfaces consumed: M001–M003 exported/modeling artifacts declared in `configs/showcase.yaml` (including M003 closeout readiness surfaces when present).
- New wiring introduced in this slice: intake generator + validation artifacts, Next.js shell app under `showcase/`, and homepage readiness panel consuming generated manifest data.
- What remains before the milestone is truly usable end-to-end: S02 executive story flow, S03 drill-down pages, and S04/S05 cross-surface continuity + hardening.

## Tasks

- [x] **T01: Define intake contract and generate blocked-aware showcase diagnostics** `est:1h 30m`
  - Why: The highest slice risk is handoff drift; we need one canonical intake truth source before rendering story UI.
  - Files: `configs/showcase.yaml`, `scripts/build_showcase_intake.py`, `src/showcase/intake_contract.py`, `tests/test_showcase_intake_contract.py`
  - Do: Add a config-driven required/optional surface contract for showcase intake, implement a generator that writes `manifest.json` and `validation_report.json` with deterministic blocked reason codes, and cover happy + missing-path branches in pytest.
  - Verify: `python -m pytest tests/test_showcase_intake_contract.py -q && python scripts/build_showcase_intake.py --config configs/showcase.yaml --output outputs/showcase/intake`
  - Done when: intake artifacts are generated locally with explicit ready/missing diagnostics and tests fail loudly on contract drift.

- [x] **T02: Scaffold the local Next.js showcase shell and intake loader boundary** `est:1h 30m`
  - Why: S01 must be demoable through a real local app runtime, not only backend scripts.
  - Files: `showcase/package.json`, `showcase/next.config.mjs`, `showcase/tsconfig.json`, `showcase/app/layout.tsx`, `showcase/app/page.tsx`, `showcase/lib/load-intake.ts`, `showcase/components/shell-status.tsx`
  - Do: Create a minimal App Router shell configured for local/static showcase use, add a typed intake loader that reads generated intake JSON with safe fallback behavior, and wire the homepage shell layout around intake status primitives.
  - Verify: `npm --prefix showcase run test -- --run && npm --prefix showcase run build`
  - Done when: `npm --prefix showcase run dev` serves a homepage shell that boots from intake data and still renders a deterministic fallback when intake files are absent.

- [x] **T03: Render visible readiness and blocked states with smoke verification** `est:1h`
  - Why: The slice demo is only true if stakeholders can immediately see what is ready vs blocked and why.
  - Files: `showcase/components/readiness-panel.tsx`, `showcase/tests/readiness-panel.test.tsx`, `showcase/tests/homepage-shell.test.tsx`, `scripts/showcase_smoke_check.py`, `docs/showcase_local_runbook.md`
  - Do: Implement readiness/blocked UI sections that list artifact paths and reason codes, add frontend tests asserting blocked-state visibility, and add a smoke script/runbook that validates homepage diagnostics over the real local entrypoint.
  - Verify: `npm --prefix showcase run test -- --run && python scripts/showcase_smoke_check.py --manifest outputs/showcase/intake/manifest.json --base-url http://127.0.0.1:3000`
  - Done when: blocked surfaces are visibly enumerated on the homepage, tests assert that behavior, and the smoke script confirms the shell exposes readiness diagnostics in a local run.

## Files Likely Touched

- `configs/showcase.yaml`
- `src/showcase/intake_contract.py`
- `scripts/build_showcase_intake.py`
- `tests/test_showcase_intake_contract.py`
- `showcase/package.json`
- `showcase/next.config.mjs`
- `showcase/tsconfig.json`
- `showcase/app/layout.tsx`
- `showcase/app/page.tsx`
- `showcase/lib/load-intake.ts`
- `showcase/components/shell-status.tsx`
- `showcase/components/readiness-panel.tsx`
- `showcase/tests/readiness-panel.test.tsx`
- `showcase/tests/homepage-shell.test.tsx`
- `scripts/showcase_smoke_check.py`
- `docs/showcase_local_runbook.md`
