from pathlib import Path

import numpy as np
import pandas as pd


def dgp_no_treat(n_i=60, T=10, sigma=0.1, seed=123):
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


def dgp_constant_te(n_i=60, T=10, te=1.0, sigma=0.1, seed=123):
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


def dgp_pretrend(n_i=60, T=10, pre_slope=0.10, sigma=0.1, seed=123):
    rng = np.random.RandomState(seed)
    rows = []
    for i in range(n_i):
        Ei = 5 if i < n_i // 2 else np.nan
        alpha = rng.normal(scale=0.2)
        for t in range(T):
            trend = 0.05 * t
            pre = pre_slope * ((t - Ei) if (not np.isnan(Ei) and t < Ei) else 0.0)
            y = alpha + trend + pre + rng.normal(scale=sigma)
            rows.append((i, t, Ei, y))
    return pd.DataFrame(rows, columns=["i", "t", "Ei", "Y"])


def main() -> None:
    out = Path("parity/out")
    out.mkdir(parents=True, exist_ok=True)
    dgp_no_treat(seed=123).to_csv(out / "dgpA_no_treat.csv", index=False)
    dgp_constant_te(seed=123).to_csv(out / "dgpB_const_te.csv", index=False)
    dgp_pretrend(seed=123).to_csv(out / "dgpC_pretrend.csv", index=False)
    print("Wrote CSVs to parity/out/*.csv")


if __name__ == "__main__":
    main()
