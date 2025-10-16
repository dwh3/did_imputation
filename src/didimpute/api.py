from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .aggregate import aggregate_event_time
from .counterfactual import compute_cell_effects
from .first_stage import FirstStageModel
from .se import attach_ses_by_k, finalize_summary_ci, pretrend_joint_test
from .utils import set_seed
from .validation import validate_and_prepare, validate_config


@dataclass
class DidImputation:
    """Imputation-based DID for staggered adoption panels.

    Parameters
    ----------
    y : str
        Outcome column name.
    id : str
        Unit identifier column.
    time : str
        Time index column (must be convertible to integers).
    Ei : str
        Adoption time column (NaN indicates never treated).
    controls : list[str] | None
        Optional list of control covariates.
    weight : str | None
        Optional non-negative weight column.
    cluster : str | None
        Cluster identifier for standard errors; defaults to ``id`` when None.
    horizons : tuple[int, int]
        Inclusive event-time horizon ``(k_min, k_max)``.
    pretrends : int
        Maximum number of negative event times used in the pretrend test.
    weight_scheme : str
        Aggregation scheme name (``nobs``, ``equal``, or ``cohort_share``).
    fe : str
        Fixed-effects configuration (reserved; currently ``twoway`` only).
    ci : float
        Confidence level for interval construction.
    minN : int
        Minimum cell count required per event time.
    random_state : int | None
        Optional seed for future stochastic routines.
    """

    y: str
    id: str
    time: str
    Ei: str
    controls: Optional[List[str]] = None
    weight: Optional[str] = None
    cluster: Optional[str] = None
    horizons: Tuple[int, int] = (-5, 10)
    pretrends: int = 5
    weight_scheme: str = "nobs"
    fe: str = "twoway"
    ci: float = 0.95
    minN: int = 10
    random_state: Optional[int] = None

    def fit(self, df: pd.DataFrame) -> "Result":
        """Run the estimator pipeline on ``df`` and return a ``Result``."""

        if self.fe != "twoway":
            if self.fe == "absorbing":
                try:
                    importlib.import_module("linearmodels")  # pragma: no cover
                except ModuleNotFoundError as exc:
                    raise ModuleNotFoundError(
                        "Absorbing fixed effects require the optional dependency 'linearmodels'. "
                        "Install it via `pip install \"didimpute[absorbing]\"`."
                    ) from exc
                raise NotImplementedError(
                    "fe='absorbing' is planned but not yet implemented. "
                    "Set fe='twoway' until support lands."
                )
            raise ValueError(f"Unsupported fixed-effects configuration: {self.fe!r}")

        if self.random_state is not None:
            set_seed(self.random_state)

        validate_config(self.horizons, self.minN, self.weight_scheme, self.ci)
        ctx = validate_and_prepare(
            df=df,
            y=self.y,
            id=self.id,
            time=self.time,
            Ei=self.Ei,
            controls=self.controls,
            weight=self.weight,
            cluster=self.cluster,
        )
        df_prepared = ctx["df"]

        first_stage = FirstStageModel().fit(
            df=df_prepared,
            y=self.y,
            id=self.id,
            time=self.time,
            controls=self.controls,
            weight=self.weight,
        )

        counterfactual = compute_cell_effects(
            df=df_prepared,
            y_col=self.y,
            id_col=self.id,
            time_col=self.time,
            Ei_col=self.Ei,
            fsm=first_stage,
            controls=self.controls,
        )

        summary = aggregate_event_time(
            df=df_prepared,
            tau=counterfactual["tau"],
            k_col="_k",
            mask=counterfactual["masks"]["treated_post"],
            cohort_col=self.Ei,
            weight_scheme=self.weight_scheme,
            horizons=self.horizons,
            minN=self.minN,
        )

        summary = attach_ses_by_k(
            df=df_prepared,
            summary=summary,
            tau=counterfactual["tau"],
            id_col=self.id,
            y_col=self.y,
            fsm=first_stage,
            treated_mask=counterfactual["masks"]["treated_post"],
        )
        summary = finalize_summary_ci(summary=summary, ci_level=self.ci)

        pretrend = pretrend_joint_test(
            df=df_prepared,
            placebo=counterfactual["placebo"],
            id_col=self.id,
            k_col="_k",
            max_negative_k=self.pretrends,
        )

        meta: Dict[str, Any] = {
            "pretrend": {
                "pvalue": pretrend[0],
                "dof": pretrend[1],
                "used_ks": pretrend[2],
            },
            "panel": ctx.get("panel_meta", {}),
            "aggregation": {
                "scheme": self.weight_scheme,
                "horizons": self.horizons,
                "minN": self.minN,
            },
        }
        intermediate: Dict[str, Any] = {
            "first_stage": first_stage.info_,
            "masks": counterfactual["masks"],
        }
        return Result(
            config=self,
            summary_df=summary,
            meta=meta,
            intermediate=intermediate,
        )


@dataclass
class Result:
    """Container for estimator outputs."""

    config: DidImputation
    summary_df: pd.DataFrame
    meta: Dict[str, Any] = field(default_factory=dict)
    intermediate: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> pd.DataFrame:
        """Return a copy of the summary table sorted by event time."""

        if self.summary_df.empty:
            return self.summary_df.copy()
        out = self.summary_df.copy()
        if "k" in out:
            out = out.sort_values("k")
        return out.reset_index(drop=True)

    def plot(self, ax: Any | None = None) -> Any:
        """Plot event-study estimates with confidence bands."""

        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError as exc:  # pragma: no cover - exercised in optional path
            raise ModuleNotFoundError(
                "Plotting requires the optional dependency 'matplotlib'. "
                "Install it via `pip install \"didimpute[plot]\"`."
            ) from exc

        if ax is None:
            ax = plt.gca()
        data = self.summary()
        if data.empty:
            ax.text(0.5, 0.5, "No results", ha="center")
            return ax
        ax.axhline(0.0, linewidth=1.0)
        ax.axvline(0.0, linewidth=1.0)
        ax.plot(data["k"], data["estimate"], marker="o")
        if {"ci_low", "ci_high"}.issubset(data.columns):
            ax.fill_between(data["k"], data["ci_low"], data["ci_high"], alpha=0.2)
        ax.set_xlabel("Event time k")
        ax.set_ylabel("Effect")
        return ax
