# didimpute (Python)

An original, audit-ready Python implementation of the imputation-based DID estimator for staggered adoption. No code or text is copied from Stata; the upstream repo is used only as a behavioral reference.

## Installation

```bash
pip install didimpute
# Enable plotting support
pip install "didimpute[plot]"
# Full extras (plotting, absorbing fixed effects, numba acceleration)
pip install "didimpute[plot,absorbing,speed]"
```

## Quickstart

```python
import pandas as pd
from didimpute import DidImputation

df = pd.read_csv("panel.csv")
est = DidImputation(y="Y", id="i", time="t", Ei="Ei", controls=["X1", "X2"])
res = est.fit(df)
print(res.summary())
```

```bash
didimpute --csv panel.csv --y Y --id i --time t --Ei Ei --controls X1,X2 `
  --scheme equal --horizons -5:10 --pretrends 5 --out summary.csv
```

## Attribution & Citation

- Software DOI and citation details: see [`CITATION.cff`](CITATION.cff) or generate via `pip install cffconvert`.
- didimpute re-implements the imputation-based DID estimator introduced in the original **[AUTHOR TBD]** paper (please replace with the canonical citation once finalized).
- Upstream Stata behaviors reference the public `did_imputation` package by **[AUTHOR TBD]**; parity scaffolding uses its published specification.

### How to cite

```
@software{didimpute,
  title        = {didimpute: Imputation-based difference-in-differences for staggered adoption},
  version      = {0.1.0},
  author       = {{didimpute contributors}},
  year         = {2025},
  url          = {https://github.com/did-imputation-port/didimpute}
}
```

## License & Notice

- Core Python implementation is released under the [MIT License](LICENSE).
- The repository retains upstream Stata reference materials in `upstream/git/` as behavioral documentation only; they are excluded from published wheels/sdists (see [NOTICE](NOTICE)).

## Reproducibility

- All shipped simulations use deterministic seeds (grid 100–149) and synthetic data generators documented in [`TEST_STRATEGY.md`](TEST_STRATEGY.md).
- The parity harness compares Python outputs against Stata reference tables; see [`docs/PARITY.md`](docs/PARITY.md) for instructions, tolerances, and interpretation.
- Golden regression tests live in `tests/golden/` and are exercised by `pytest` in CI for release parity.

## Support / Issues

Please open issues or feature requests at <https://github.com/did-imputation-port/didimpute/issues>. Pull requests are welcome once you review [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Additional Resources

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — high-level data flow and component responsibilities.
- [`ROADMAP.md`](ROADMAP.md) — planned feature development.
- [`DECISIONS.md`](DECISIONS.md) — design and governance ADRs.
- [`docs/PARITY.md`](docs/PARITY.md) — full parity validation narrative.
