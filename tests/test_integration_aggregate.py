from __future__ import annotations

import numpy as np
import pandas as pd

from didimpute import DidImputation


def test_end_to_end_through_aggregation() -> None:
    """Ensure the estimator runs through aggregation and returns expected columns."""

    rows = []
    for i in range(12):
        Ei = 3 if i < 6 else np.nan
        for t in range(6):
            treatment_effect = 0.5 if (not np.isnan(Ei) and t >= Ei) else 0.0
            rows.append((i, t, Ei, treatment_effect))
    df = pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])

    result = DidImputation(y="Y", id="i", time="t", Ei="Ei", horizons=(-1, 2), minN=1).fit(df)
    summary = result.summary()

    assert {"k", "estimate", "n", "weight_scheme"}.issubset(summary.columns)
