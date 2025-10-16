from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from .errors import EstimationError


def _unique_in_order(values: Sequence[Any]) -> List[Any]:
    """Return the unique elements of ``values`` preserving first appearance."""

    seen: Dict[Any, None] = {}
    for value in values:
        if value not in seen:
            seen[value] = None
    return list(seen.keys())


@dataclass
class FirstStageModel:
    """
    Weighted two-way fixed-effects regression fit on the untreated sample.

    The model includes an intercept, optional controls, and unit/time dummies
    (using the first observed categories as baselines).
    """

    fitted_: bool = False
    info_: Dict[str, Any] = field(default_factory=dict)
    coef_: Optional[NDArray[np.float64]] = None
    design_columns_: List[str] = field(default_factory=list)
    controls_: List[str] = field(default_factory=list)
    id_baseline_: Any = None
    id_levels_: List[Any] = field(default_factory=list)
    time_baseline_: Any = None
    time_levels_: List[Any] = field(default_factory=list)
    id_col_: Optional[str] = None
    time_col_: Optional[str] = None
    xtwx_inv_: Optional[NDArray[np.float64]] = None
    untreated_design_: Optional[NDArray[np.float64]] = None
    untreated_weights_: Optional[NDArray[np.float64]] = None
    untreated_ids_: Optional[NDArray[Any]] = None
    untreated_residuals_: Optional[NDArray[np.float64]] = None

    def fit(
        self,
        df: pd.DataFrame,
        y: str,
        id: str,
        time: str,
        controls: Optional[List[str]],
        weight: Optional[str],
    ) -> "FirstStageModel":
        """
        Estimate the untreated regression using weighted least squares.

        Parameters
        ----------
        df : pd.DataFrame
            Prepared panel with helper columns from ``validate_and_prepare``.
        y, id, time : str
            Outcome, unit id, and time column names.
        controls : list[str] | None
            Optional control variable names.
        weight : str | None
            Optional weight column; falls back to ``_w`` when absent.

        Raises
        ------
        EstimationError
            If the untreated sample is empty, weights are invalid, or the
            design matrix is rank deficient.
        """

        untreated = df[df["_untreated"] == 1].copy()
        if untreated.empty:
            raise EstimationError("Untreated sample is empty; cannot fit first stage.")

        weights = untreated["_w"].to_numpy(dtype=float)
        if weight:
            weights = pd.to_numeric(untreated[weight], errors="coerce").to_numpy(dtype=float)

        if np.any(weights < 0):
            raise EstimationError("Weights must be non-negative in the first stage.")
        if not np.any(weights > 0):
            raise EstimationError("At least one untreated observation must carry positive weight.")

        self.controls_ = [c for c in (controls or [])]
        self.id_col_ = id
        self.time_col_ = time

        id_values = untreated[id].to_numpy()
        time_values = untreated[time].to_numpy()
        id_levels = _unique_in_order(id_values.tolist())
        time_levels = _unique_in_order(time_values.tolist())
        if not id_levels or not time_levels:
            raise EstimationError("Insufficient variation in id or time for the first stage.")

        self.id_baseline_ = id_levels[0]
        self.time_baseline_ = time_levels[0]
        self.id_levels_ = [lvl for lvl in id_levels if lvl != self.id_baseline_]
        self.time_levels_ = [lvl for lvl in time_levels if lvl != self.time_baseline_]

        design = self._build_design_matrix(untreated, fit_mode=True)
        y_vec = pd.to_numeric(untreated[y], errors="coerce").to_numpy(dtype=float)
        if np.isnan(y_vec).any():
            raise EstimationError("Outcome contains non-numeric values in the untreated sample.")

        sqrt_w = np.sqrt(weights)
        design_w = design * sqrt_w[:, None]
        y_w = y_vec * sqrt_w

        coef, residuals, rank, _sing = np.linalg.lstsq(design_w, y_w, rcond=None)
        if rank < design.shape[1]:
            raise EstimationError("First-stage design matrix is rank deficient.")

        xtwx = design_w.T @ design_w
        try:
            xtwx_inv = np.linalg.inv(xtwx)
        except np.linalg.LinAlgError as exc:
            raise EstimationError("Unable to invert first-stage information matrix.") from exc

        self.coef_ = coef.astype(float)
        self.xtwx_inv_ = xtwx_inv.astype(float)
        residuals_untreated = y_vec - design @ self.coef_
        self.untreated_design_ = design.astype(float, copy=True)
        self.untreated_weights_ = weights.astype(float, copy=True)
        self.untreated_ids_ = untreated[id].to_numpy()
        self.untreated_residuals_ = residuals_untreated.astype(float, copy=True)
        self.design_columns_ = self._design_column_names()
        self.info_ = {
            "n_obs": int(len(untreated)),
            "rank": int(rank),
            "controls": list(self.controls_),
            "baseline_id": self.id_baseline_,
            "baseline_time": self.time_baseline_,
        }
        self.fitted_ = True
        return self

    def predict_y0(
        self,
        df: pd.DataFrame,
        y: str,
        id: str,
        time: str,
        controls: Optional[List[str]],
    ) -> NDArray[np.float64]:
        """
        Predict counterfactual untreated outcomes for all observations in ``df``.

        Raises
        ------
        EstimationError
            If the model has not been fitted or unseen identifiers/time indices appear.
        """

        _ = y  # maintained for API parity
        if not self.fitted_:
            raise EstimationError("First-stage model is not fitted.")

        if id != self.id_col_ or time != self.time_col_:
            raise EstimationError("Column names differ from the fitted configuration.")

        if controls and controls != self.controls_:
            raise EstimationError("Control specification changed between fit and predict.")

        if self.coef_ is None:
            raise EstimationError("First-stage coefficients are unavailable.")

        design = self._build_design_matrix(df, fit_mode=False)
        return design @ self.coef_

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _design_column_names(self) -> List[str]:
        """Return ordered column names for diagnostics."""

        cols = ["intercept"]
        cols.extend(self.controls_)
        cols.extend([f"id::{lvl}" for lvl in self.id_levels_])
        cols.extend([f"time::{lvl}" for lvl in self.time_levels_])
        return cols

    def _build_design_matrix(self, frame: pd.DataFrame, fit_mode: bool) -> NDArray[np.float64]:
        """Construct the two-way fixed-effects design matrix."""

        n = len(frame)
        if n == 0:
            return np.empty((0, 0), dtype=float)

        pieces: List[NDArray[np.float64]] = [np.ones((n, 1), dtype=float)]

        if self.controls_:
            controls_block = frame[self.controls_].apply(pd.to_numeric, errors="coerce")
            if controls_block.isnull().any().any():
                raise EstimationError("Controls must be numeric for first-stage estimation.")
            pieces.append(controls_block.to_numpy(dtype=float))

        id_series = frame[self.id_col_].to_numpy()
        time_series = frame[self.time_col_].to_numpy()

        if not fit_mode:
            valid_ids = set(self.id_levels_ + [self.id_baseline_])
            unseen_ids = sorted(set(id_series.tolist()) - valid_ids)
            if unseen_ids:
                raise EstimationError(
                    f"Encountered unseen unit ids during prediction: {unseen_ids}",
                )

            valid_times = set(self.time_levels_ + [self.time_baseline_])
            unseen_times = sorted(set(time_series.tolist()) - valid_times)
            if unseen_times:
                raise EstimationError(
                    f"Encountered unseen time indices during prediction: {unseen_times}",
                )

        if self.id_levels_:
            id_dummies = [
                (id_series == level).astype(float).reshape(-1, 1) for level in self.id_levels_
            ]
            pieces.append(np.hstack(id_dummies) if id_dummies else np.empty((n, 0)))
        if self.time_levels_:
            time_dummies = [
                (time_series == level).astype(float).reshape(-1, 1) for level in self.time_levels_
            ]
            pieces.append(np.hstack(time_dummies) if time_dummies else np.empty((n, 0)))

        if len(pieces) == 1:
            raise EstimationError(
                "Design matrix lacks regressors; check untreated sample variation.",
            )

        return np.hstack(pieces)

    def design_matrix(self, frame: pd.DataFrame) -> NDArray[np.float64]:
        """Public helper to obtain the design matrix for ``frame``."""

        if not self.fitted_:
            raise EstimationError("First-stage model is not fitted.")
        return self._build_design_matrix(frame, fit_mode=False)
