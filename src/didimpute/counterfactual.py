from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .first_stage import FirstStageModel


def compute_cell_effects(
    df: pd.DataFrame,
    y_col: str,
    id_col: str,
    time_col: str,
    Ei_col: str,
    fsm: FirstStageModel,
    controls: Optional[List[str]],
) -> Dict[str, Any]:
    """
    Compute fitted counterfactuals and resulting cell-level effects.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared panel returned by :func:`validate_and_prepare`.
    y_col, id_col, time_col, Ei_col : str
        Column labels for the outcome, unit, time index, and adoption time.
    fsm : FirstStageModel
        Fitted first-stage model available via :meth:`FirstStageModel.fit`.
    controls : list[str] | None
        Optional list of control columns (kept for parity with future versions).

    Returns
    -------
    dict[str, Any]
        ``y0_hat`` fitted counterfactuals; ``tau`` for treated-post cells; ``placebo`` for
        eventual-treated pre-periods; ``masks`` with boolean selectors used downstream.
    """

    y_hat0 = fsm.predict_y0(df, y_col, id_col, time_col, controls)
    outcome = df[y_col].astype(float).to_numpy()

    time_vals = df[time_col].to_numpy()
    adoption_vals = df[Ei_col].to_numpy()
    finite_adoption = df["_Ei_finite"].to_numpy(dtype=bool)
    untreated_mask = df["_untreated"].to_numpy(dtype=bool)

    treated_post = finite_adoption & (time_vals >= adoption_vals)
    treated_pre = finite_adoption & (time_vals < adoption_vals)

    tau = np.full_like(outcome, np.nan, dtype=float)
    tau[treated_post] = outcome[treated_post] - y_hat0[treated_post]

    placebo = np.full_like(outcome, np.nan, dtype=float)
    placebo[treated_pre] = outcome[treated_pre] - y_hat0[treated_pre]

    masks = {
        "treated_post": treated_post,
        "treated_pre": treated_pre,
        "never_treated": ~finite_adoption,
        "untreated_all": untreated_mask,
    }

    return {
        "y0_hat": y_hat0,
        "tau": tau,
        "placebo": placebo,
        "masks": masks,
    }
