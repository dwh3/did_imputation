from __future__ import annotations

import numpy as np
import pandas as pd

from didimpute.aggregate import aggregate_event_time


def _toy_panel() -> tuple[pd.DataFrame, np.ndarray]:
    """Construct a panel with two treated cohorts and preset event-time effects."""

    rows = []
    for i in range(10):
        Ei = 3 if i < 6 else 4
        for t in range(7):
            rows.append((i, t, Ei, np.nan))
    df = pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])
    df["_Ei_finite"] = True
    df["_k"] = df["t"] - df["Ei"]
    df["_T"] = (df["_k"] >= 0).astype(int)
    df["_untreated"] = 1 - df["_T"]

    tau = np.full(len(df), np.nan)
    mask = (df["_T"] == 1) & (df["_k"] == 1)
    tau[mask.values] = np.where(df.loc[mask, "Ei"].to_numpy() == 3, 1.0, 2.0)
    return df, tau


def test_weighting_differences() -> None:
    """Check aggregation schemes produce expected weighting relationships."""

    df, tau = _toy_panel()
    treated_mask = (df["_T"] == 1).to_numpy(dtype=bool)

    summaries = {}
    for scheme in ["nobs", "equal", "cohort_share"]:
        result = aggregate_event_time(df, tau, "_k", treated_mask, "Ei", scheme, (1, 1), 1)
        assert {"k", "estimate", "n", "weight_scheme"}.issubset(result.columns)
        assert len(result) == 1
        summaries[scheme] = result["estimate"].iloc[0]

    assert abs(summaries["equal"] - 1.5) < 1e-8
    assert abs(summaries["nobs"] - summaries["cohort_share"]) < 1e-8
