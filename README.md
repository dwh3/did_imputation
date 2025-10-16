# didimpute (Python)

`didimpute` provides an imputation-based difference-in-differences estimator for staggered adoption settings, ported from the original Stata implementation.

## Install

```powershell
pip install didimpute
```

From a local checkout, install in editable mode with `[speed]` extras to enable optional `numba` acceleration:

```powershell
pip install -e .[speed]
```

## Quickstart

```python
import pandas as pd
from didimpute import DidImputation

df = pd.DataFrame(
    {"i": [1, 1, 2, 2], "t": [0, 1, 0, 1], "Ei": [1, 1, float("nan"), float("nan")], "Y": [0.0, 1.0, 0.0, 0.9]}
)
est = DidImputation(y="Y", id="i", time="t", Ei="Ei", horizons=(-1, 1), minN=1).fit(df)
print(est.summary())
```

See the documentation for a full tutorial and model diagnostics.

## Citation

If `didimpute` supports your research, cite the software using the metadata in `CITATION.cff`.

## License

This project is released under the MIT License. See `LICENSE` for the full text.

## Reproducibility

- All core dependencies are pinned in `pyproject.toml`.
- Linting, type checks, tests, docs, and packaging gates are executable via the commands listed in the project README and `STATUS.md` artifacts.
- Optional performance enhancements live under the `speed` extra to avoid coupling replayable environments to JIT dependencies.
