from __future__ import annotations

import numpy as np
import pandas as pd

from didimpute import DidImputation


def _dgp_constant_te() -> pd.DataFrame:
    """Construct a simple panel with constant treatment effect post adoption."""

    rows = []
    for i in range(20):
        Ei = 3 if i < 10 else np.nan
        for t in range(7):
            te = 0.5 if (not np.isnan(Ei) and t >= Ei) else 0.0
            rows.append((i, t, Ei, te))
    return pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])


def test_end_to_end_with_ses_and_pretrend() -> None:
    """Estimator should populate SEs, CIs, and pretrend metadata."""

    df = _dgp_constant_te()
    result = DidImputation(
        y="Y",
        id="i",
        time="t",
        Ei="Ei",
        horizons=(-2, 3),
        pretrends=2,
        minN=1,
    ).fit(df)
    summary = result.summary()
    assert {"k", "estimate", "se", "ci_low", "ci_high", "n"}.issubset(summary.columns)
    assert "pretrend" in result.meta
