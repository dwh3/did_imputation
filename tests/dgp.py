from __future__ import annotations

import numpy as np
import pandas as pd


def dgp_no_treat(
    n_i: int = 60,
    T: int = 10,
    sigma: float = 0.1,
    seed: int = 123,
) -> pd.DataFrame:
    """Never-treated panel with unit intercepts and linear time trend."""

    rng = np.random.RandomState(seed)
    rows = []
    for i in range(n_i):
        Ei = np.nan
        alpha = rng.normal(scale=0.2)
        for t in range(T):
            lam = 0.05 * t
            y = alpha + lam + rng.normal(scale=sigma)
            rows.append((i, t, Ei, y))
    return pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])


def dgp_constant_te(
    n_i: int = 60,
    T: int = 10,
    te: float = 1.0,
    sigma: float = 0.1,
    seed: int = 123,
) -> pd.DataFrame:
    """Half the units adopt at period 5 with constant treatment effect thereafter."""

    rng = np.random.RandomState(seed)
    rows = []
    for i in range(n_i):
        Ei = 5 if i < n_i // 2 else np.nan
        alpha = rng.normal(scale=0.2)
        for t in range(T):
            lam = 0.05 * t
            tau = te if (not np.isnan(Ei) and t >= Ei) else 0.0
            y = alpha + lam + tau + rng.normal(scale=sigma)
            rows.append((i, t, Ei, y))
    return pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])


def dgp_pretrend(
    n_i: int = 60,
    T: int = 10,
    te: float = 0.0,
    pre_slope: float = 0.10,
    sigma: float = 0.1,
    seed: int = 123,
) -> pd.DataFrame:
    """Units slated for treatment exhibit drifting pre-trends prior to adoption."""

    rng = np.random.RandomState(seed)
    rows = []
    for i in range(n_i):
        Ei = 5 if i < n_i // 2 else np.nan
        alpha = rng.normal(scale=0.2)
        for t in range(T):
            trend = 0.05 * t
            pre = pre_slope * ((t - Ei) if (not np.isnan(Ei) and t < Ei) else 0.0)
            tau = te if (not np.isnan(Ei) and t >= Ei) else 0.0
            y = alpha + trend + pre + tau + rng.normal(scale=sigma)
            rows.append((i, t, Ei, y))
    return pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])
