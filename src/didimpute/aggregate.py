from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def _agg_cell_mean(data: pd.DataFrame) -> pd.DataFrame:
    """Simple average across treated cells for each event time."""

    grouped = data.groupby("k", sort=True)
    estimate = grouped["tau"].mean().rename("estimate")
    nobs = grouped.size().rename("n")
    return pd.concat([estimate, nobs], axis=1).reset_index()


def _agg_cohort_equal(data: pd.DataFrame) -> pd.DataFrame:
    """Equal weight across cohorts after averaging within each cohort."""

    within = (
        data.groupby(["k", "cohort"], sort=True)["tau"]
        .mean()
        .rename("mu_gk")
        .reset_index()
    )
    estimate = within.groupby("k", sort=True)["mu_gk"].mean().rename("estimate")
    nobs = data.groupby("k", sort=True).size().rename("n")
    return pd.concat([estimate, nobs], axis=1).reset_index()


def _agg_cohort_share(data: pd.DataFrame) -> pd.DataFrame:
    """Weight cohort means by their share of treated cells at each event time."""

    counts = (
        data.groupby(["k", "cohort"], sort=True)
        .size()
        .rename("n_gk")
        .reset_index()
    )
    means = (
        data.groupby(["k", "cohort"], sort=True)["tau"]
        .mean()
        .rename("mu_gk")
        .reset_index()
    )
    merged = pd.merge(means, counts, on=["k", "cohort"], how="inner")
    merged["N_k"] = merged.groupby("k")["n_gk"].transform("sum")
    merged["weight"] = merged["n_gk"] / merged["N_k"]
    merged["wmu"] = merged["weight"] * merged["mu_gk"]

    estimate = merged.groupby("k", sort=True)["wmu"].sum().rename("estimate")
    nobs = data.groupby("k", sort=True).size().rename("n")
    return pd.concat([estimate, nobs], axis=1).reset_index()


def aggregate_event_time(
    df: pd.DataFrame,
    tau: np.ndarray,
    k_col: str,
    mask: np.ndarray,
    cohort_col: str,
    weight_scheme: str,
    horizons: Tuple[int, int],
    minN: int,
) -> pd.DataFrame:
    """
    Aggregate cell-level effects to event time using the requested weighting scheme.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared panel (output of ``validate_and_prepare``).
    tau : np.ndarray
        Cell-level effects aligned with ``df``.
    k_col : str
        Column containing event time ``k``.
    mask : np.ndarray
        Boolean mask selecting treated-post cells to include.
    cohort_col : str
        Cohort identifier, typically the adoption time ``Ei``.
    weight_scheme : str
        One of ``{"nobs", "equal", "cohort_share"}``.
    horizons : tuple[int, int]
        Inclusive event-time range to retain.
    minN : int
        Minimum number of cells required at a given ``k``.

    Returns
    -------
    pd.DataFrame
        Columns ``[k, estimate, n, weight_scheme]`` (possibly empty).
    """

    tau_arr = np.asarray(tau, dtype=float)
    k_values = np.asarray(df[k_col].to_numpy(), dtype=float)
    mask_arr = np.asarray(mask, dtype=bool)
    cohort_values = df[cohort_col].to_numpy()

    valid = mask_arr & np.isfinite(tau_arr) & np.isfinite(k_values)
    if cohort_values.dtype.kind in {"f", "i"}:
        valid &= np.isfinite(cohort_values.astype(float))
    else:
        valid &= pd.notna(cohort_values)

    if not np.any(valid):
        return pd.DataFrame(columns=["k", "estimate", "n", "weight_scheme"])

    data = pd.DataFrame(
        {
            "k": k_values[valid].astype(int),
            "tau": tau_arr[valid],
            "cohort": cohort_values[valid],
        },
    )

    k_min, k_max = horizons
    data = data[(data["k"] >= k_min) & (data["k"] <= k_max)]
    data = data[data["cohort"].notna()]
    if data.empty:
        return pd.DataFrame(columns=["k", "estimate", "n", "weight_scheme"])

    if weight_scheme == "nobs":
        aggregated = _agg_cell_mean(data)
    elif weight_scheme == "equal":
        aggregated = _agg_cohort_equal(data)
    elif weight_scheme == "cohort_share":
        aggregated = _agg_cohort_share(data)
    else:  # pragma: no cover - guarded by validate_config
        raise ValueError(f"Unknown weight_scheme: {weight_scheme}")

    aggregated = aggregated[aggregated["n"] >= minN].copy()
    if aggregated.empty:
        return pd.DataFrame(columns=["k", "estimate", "n", "weight_scheme"])

    aggregated["weight_scheme"] = weight_scheme
    aggregated["n"] = aggregated["n"].astype(int)
    return aggregated.sort_values("k").reset_index(drop=True)
