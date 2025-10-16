# Contributing
- Branch: feature/<short>; Conventional commits: feat:, fix:, docs:, test:, chore:
- **Gates**: `ruff check .` (incl. import-sorting), `mypy --strict src/didimpute`, `pytest -q`
- **Docstrings**: Every public class/function must have a NumPy/Google-style docstring.
- Keep ARCHITECTURE, SPEC, TEST_STRATEGY, ROADMAP, DECISIONS in sync with code changes.
