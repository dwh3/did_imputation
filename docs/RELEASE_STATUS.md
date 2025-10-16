# didimpute v0.1.0 — Release Status

## Preflight Results (2025-10-14)
- ✅ `.venv/Scripts/python.exe -m ruff check`
- ✅ `.venv/Scripts/python.exe -m mypy --strict src`
- ✅ `.venv/Scripts/python.exe -m pytest -q --cov --cov-report=term` → total coverage **91%** (modules `api` 77%, `utils` 69% need extra tests)
- ✅ `.venv/Scripts/python.exe -m mkdocs build --strict` (nav enabled via new `mkdocs.yml`)

## Documentation Assessment
- Strengths: README offers concise API/CLI snippets; SPEC and PARITY docs outline estimator behavior and validation harness; ROADMAP/DECISIONS enumerate scope and future work.
- Gaps blocking release polish:
  1. README lacks installation guidance (`pip install`, supported Python versions), license synopsis, citation of the original DID research, release DOI/contact, and guidance on reproducibility expectations.
  2. No contributor-facing or user-facing instructions for rerunning the parity harness (Stata dependency, expected environment variables, seed handling, parity/out artifacts).
  3. ARCHITECTURE.md is too terse for new contributors (needs component responsibilities, data flow, and error propagation details).
  4. Docs do not describe data generation scripts, deterministic seeds, or how to reproduce coverage/parity claims; add a reproducibility checklist.
  5. Missing citation or acknowledgement file (e.g., `CITATION.cff`) and cross-links from docs to LICENSE and TEST_STRATEGY.

## Packaging & Metadata
- `pyproject.toml` omits PyPI classifiers (Python versions, intended audience, license), project URLs (homepage/docs/source/issues), and keywords; add before release.
- Hatch build config is absent, so the sdist currently bundles parity logs, CSV outputs, and upstream Stata sources (`parity/out/*`, `*_stata.log`, `tmp_old.txt`, etc.). Prune these via `tool.hatch.build` (or MANIFEST) to keep the distribution lean and avoid machine-specific artifacts.
- Confirm whether shipping GPL-licensed Stata sources inside `upstream/git/` is necessary; if retained, document licensing segregation and ensure compliance (dual-license notice, attribution in README/docs).
- Validate that wheel metadata exposes long description/content type (OK) and add maintainer info if applicable.

## Ethical & Reproducibility Review
- Document synthetic data generation, random-seed policy (currently seeds 100..149), and how to recreate regression goldens.
- Clarify external tooling requirements (e.g., Stata 18 path) and expected environment variables in parity documentation to ensure reproducibility without leaking machine-specific paths.
- State explicitly that no proprietary datasets/code are shipped; ensure parity outputs do not embed licensed Stata material beyond what’s permitted.

## Repository Hygiene
- Remove or ignore locally generated logs and parity outputs (`*_stata.log`, `peek*.log`, `parity/out/*.csv`, `_tmp.log`, `tmp_old.txt`, `debug.log`) before tagging the release.
- Drop built artifacts (`dist/`) from version control; rely on CI/CLI build steps instead.
- Ensure `.venv/` stays untracked and consider adding `docs/site/` (mkdocs output) to `.gitignore` if publishing docs separately.
- Add automated audit (pre-commit or CI) to prevent large binaries/logs from entering future dists.

## Recommendation
- ⚠️ **Needs polish before public release.**
- Prioritize: (1) documentation refresh (installation, licensing, parity reproducibility, architecture detail, citation/contact), (2) packaging cleanup (metadata + sdist pruning + license clarification), (3) hygiene sweep to drop logs/artifacts and add guardrails, (4) bolster tests around low-covered modules (`api`, `utils`).
