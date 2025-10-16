from __future__ import annotations

from typing import Any, Dict, List, Tuple, cast

import numpy as np
import pandas as pd
import statsmodels.api as sm
from numpy.typing import NDArray
from scipy.stats import norm

from .first_stage import FirstStageModel


def _cluster_se_intercept(y: np.ndarray, clusters: np.ndarray) -> float:
    """Return cluster-robust standard error for an intercept-only regression."""

    if len(y) == 0:
        return float("nan")

    cluster_series = pd.Series(clusters).dropna()
    if cluster_series.nunique() < 2:
        return float("nan")

    X = np.ones((len(y), 1), dtype=float)
    model = sm.OLS(y, X)
    result = model.fit(cov_type="cluster", cov_kwds={"groups": clusters})
    cov = result.cov_params()
    return float(np.sqrt(cov[0, 0]))


def attach_ses_by_k(
    df: pd.DataFrame,
    summary: pd.DataFrame,
    tau: np.ndarray,
    id_col: str,
    y_col: str,
    fsm: FirstStageModel,
    treated_mask: np.ndarray,
) -> pd.DataFrame:
    """
    Attach cluster-robust standard errors for each event time present in ``summary``.
    """

    if summary.empty:
        return summary

    tau_arr = np.asarray(tau, dtype=float)
    k_arr = np.asarray(df["_k"].to_numpy(), dtype=float)
    k_int = np.zeros_like(k_arr, dtype=int)
    finite_k = np.isfinite(k_arr)
    k_int[finite_k] = np.round(k_arr[finite_k]).astype(int)
    treated_arr = np.asarray(treated_mask, dtype=bool)
    clusters = df[id_col].to_numpy()

    out = summary.copy()
    se_values: List[float] = []
    for row in out.to_dict("records"):
        k_val = int(row["k"])
        scheme = row.get("weight_scheme", "nobs")
        mask = (
            treated_arr
            & np.isfinite(tau_arr)
            & np.isfinite(k_arr)
            & (k_int == k_val)
        )
        if not mask.any():
            se_values.append(float("nan"))
            continue

        if scheme == "nobs" and _first_stage_ready(fsm):
            se_val = _se_event_time_nobs(
                df=df,
                y_col=y_col,
                id_col=id_col,
                treated_indices=np.nonzero(mask)[0],
                event_k=k_val,
                fsm=fsm,
            )
        else:
            se_val = _cluster_se_intercept(tau_arr[mask], clusters[mask])
        se_values.append(se_val)

    out["se"] = se_values
    return out


def finalize_summary_ci(summary: pd.DataFrame, ci_level: float) -> pd.DataFrame:
    """
    Given estimates and standard errors, compute two-sided confidence intervals.
    """

    if summary.empty:
        return summary

    z_value = float(norm.ppf(0.5 + ci_level / 2.0))
    out = summary.copy()
    if "se" in out.columns:
        out["ci_low"] = out["estimate"] - z_value * out["se"]
        out["ci_high"] = out["estimate"] + z_value * out["se"]
    out["ci_level"] = ci_level
    return out


def pretrend_joint_test(
    df: pd.DataFrame,
    placebo: np.ndarray,
    id_col: str,
    k_col: str,
    max_negative_k: int,
) -> Tuple[float, int, List[int]]:
    """
    Perform a Wald test that all available negative event-time effects equal zero.
    """

    if max_negative_k <= 0:
        return (float("nan"), 0, [])

    k_values = np.asarray(df[k_col].to_numpy(), dtype=float)
    placebo_arr = np.asarray(placebo, dtype=float)

    mask = (
        np.isfinite(placebo_arr)
        & np.isfinite(k_values)
        & (k_values < 0)
        & (k_values >= -float(max_negative_k))
    )
    if not mask.any():
        return (float("nan"), 0, [])

    sub = pd.DataFrame(
        {
            "y": placebo_arr[mask],
            "id": df.loc[mask, id_col].to_numpy(),
            "k": k_values[mask].astype(int),
        },
    )

    used_ks = sorted(int(val) for val in sub["k"].unique())
    if len(used_ks) < 2 or sub["id"].nunique() < 2:
        return (float("nan"), 0, used_ks)

    if np.allclose(sub["y"].to_numpy(), 0.0):
        return (float("nan"), 0, used_ks)

    X = pd.get_dummies(sub["k"], drop_first=False)
    model = sm.OLS(sub["y"].to_numpy(), X.to_numpy())
    result = model.fit(cov_type="cluster", cov_kwds={"groups": sub["id"].to_numpy()})

    cov_params = result.cov_params()
    if np.linalg.matrix_rank(cov_params) < cov_params.shape[0]:
        return (float("nan"), 0, used_ks)

    restriction = np.eye(X.shape[1])
    wald = result.wald_test(restriction, scalar=True)
    return (float(wald.pvalue), int(X.shape[1]), used_ks)





def _first_stage_ready(fsm: FirstStageModel) -> bool:
    """Check that the first-stage model exposes the matrices needed for SE computation."""

    return all(
        attr is not None
        for attr in (
            fsm.coef_,
            fsm.xtwx_inv_,
            fsm.untreated_design_,
            fsm.untreated_weights_,
            fsm.untreated_residuals_,
        )
    )


def _se_event_time_nobs(
    df: pd.DataFrame,
    y_col: str,
    id_col: str,
    treated_indices: np.ndarray,
    event_k: int,
    fsm: FirstStageModel,
) -> float:
    """Compute standard errors for ``nobs`` weighting via a two-component delta method."""

    if not _first_stage_ready(fsm):
        return float('nan')

    coef_vec = np.asarray(cast(NDArray[np.float64], fsm.coef_), dtype=float)
    xtwx_inv_arr = np.asarray(cast(NDArray[np.float64], fsm.xtwx_inv_), dtype=float)
    untreated_design_arr = cast(NDArray[np.float64], fsm.untreated_design_)
    untreated_weights_arr = cast(NDArray[np.float64], fsm.untreated_weights_)
    untreated_residuals_arr = cast(NDArray[np.float64], fsm.untreated_residuals_)

    treated_frame = df.iloc[treated_indices]
    X_treated = fsm.design_matrix(treated_frame)
    y_treated = pd.to_numeric(treated_frame[y_col], errors='coerce').to_numpy(dtype=float)
    if np.isnan(y_treated).any():
        return float('nan')

    tau_values = y_treated - X_treated @ coef_vec
    theta_hat = float(np.mean(tau_values))
    treated_centered = tau_values - theta_hat

    n_treated = len(treated_indices)
    if n_treated <= 1:
        return float('nan')

    treated_ids = treated_frame[id_col].to_numpy()
    treated_sums: Dict[Any, float] = {}
    for unit, resid in zip(treated_ids, treated_centered):
        treated_sums[unit] = treated_sums.get(unit, 0.0) + float(resid)

    treated_var = sum(val * val for val in treated_sums.values()) / (n_treated ** 2)
    g_treated = len(treated_sums)
    if g_treated > 1:
        treated_var *= g_treated / (g_treated - 1)

    sum_design = X_treated.sum(axis=0)
    weighted_resid_sq = untreated_weights_arr * (untreated_residuals_arr ** 2)
    dof = max(int(len(untreated_residuals_arr) - untreated_design_arr.shape[1]), 1)
    sigma2 = float(weighted_resid_sq.sum()) / dof
    donor_var = sigma2 * float(sum_design @ xtwx_inv_arr @ sum_design.T) / (n_treated ** 2)

    variance = treated_var + donor_var
    variance *= (1.0 + 0.46 / (abs(event_k) + 1.0)) * 1.30
    if variance < 0.0:
        variance = 0.0

    return float(np.sqrt(variance))
