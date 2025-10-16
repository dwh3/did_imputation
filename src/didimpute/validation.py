from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .errors import ValidationError


def validate_config(
    horizons: Tuple[int, int],
    minN: int,
    scheme: str,
    ci: float,
) -> None:
    """
    Validate high-level configuration parameters.

    Raises
    ------
    ValidationError
        If any range or option is invalid.
    """

    k_min, k_max = horizons
    if k_min > k_max:
        raise ValidationError(
            "Invalid horizons: require k_min <= k_max (for example, --horizons -5:10).",
        )
    if minN < 1:
        raise ValidationError(
            "minN must be at least one. Consider lowering the threshold or widening horizons.",
        )
    if scheme not in {"nobs", "equal", "cohort_share"}:
        raise ValidationError(
            "weight_scheme must be one of {'nobs','equal','cohort_share'}.",
        )
    if not 0.0 < ci < 1.0:
        raise ValidationError("ci must lie in (0,1); for example, 0.95.")


def _ensure_columns(df: pd.DataFrame, cols: List[str]) -> None:
    """Raise ValidationError if the DataFrame is missing required columns."""

    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValidationError(
            f"Missing required columns: {missing}. Provide these via --y/--id/--time/--Ei.",
        )


def validate_and_prepare(
    df: pd.DataFrame,
    y: str,
    id: str,
    time: str,
    Ei: str,
    controls: Optional[List[str]],
    weight: Optional[str],
    cluster: Optional[str],
) -> Dict[str, Any]:
    """
    Validate the input panel and construct helper columns consumed by the pipeline.

    Returns
    -------
    dict[str, Any]
        A dictionary with keys ``df`` (prepared copy) and ``panel_meta`` (balance diagnostics).

    Raises
    ------
    ValidationError
        If required columns are missing, types are incompatible, duplicates exist, weights are
        negative, or the untreated sample is empty.
    """

    _ensure_columns(df, [y, id, time, Ei])
    if controls:
        control_missing = [col for col in controls if col not in df.columns]
        if control_missing:
            raise ValidationError(
                f"Control columns not found: {control_missing}. "
                "Fix column names or adjust --controls.",
            )
    if weight and weight not in df.columns:
        raise ValidationError(f"Weight column '{weight}' not found.")
    if cluster and cluster not in df.columns:
        raise ValidationError(f"Cluster column '{cluster}' not found.")

    prepared = df.copy()

    # Coerce time to integers.
    try:
        prepared[time] = pd.to_numeric(prepared[time]).astype(int)
    except Exception as exc:  # pragma: no cover - re-raised with context
        raise ValidationError(
            f"Time column '{time}' must be integer-castable. Clean or cast before calling fit(). "
            f"Original error: {exc}",
        ) from exc

    # Coerce Ei to numeric (NaN allowed to flag never-treated units).
    try:
        prepared[Ei] = pd.to_numeric(prepared[Ei], errors="coerce")
    except Exception as exc:  # pragma: no cover - re-raised with context
        raise ValidationError(
            f"Ei column must be numeric or NaN for never-treated units. Original error: {exc}",
        ) from exc

    # Detect duplicate (id, time) pairs.
    duplicate_mask = prepared.duplicated([id, time])
    if bool(duplicate_mask.any()):
        sample = prepared.loc[duplicate_mask, [id, time]].head(5).to_dict("records")
        raise ValidationError(
            "Duplicate (id, time) rows detected (first five shown): "
            f"{sample}. Deduplicate or aggregate prior to estimation.",
        )

    # Event-time bookkeeping.
    prepared["_Ei_finite"] = prepared[Ei].notna() & np.isfinite(prepared[Ei])
    prepared.loc[prepared["_Ei_finite"], Ei] = (
        prepared.loc[prepared["_Ei_finite"], Ei].astype(int)
    )
    prepared["_k"] = np.where(prepared["_Ei_finite"], prepared[time] - prepared[Ei], np.nan)

    # Treatment status and untreated indicator.
    treated = prepared["_Ei_finite"] & (prepared[time] >= prepared[Ei])
    prepared["_T"] = treated.astype(int)
    prepared["_untreated"] = (~treated).astype(int)

    # Weights (default 1.0).
    if weight:
        weights = pd.to_numeric(prepared[weight], errors="coerce").astype(float)
        if (weights < 0).any():
            raise ValidationError(
                "Weights must be non-negative. Replace negatives with zero or drop affected rows.",
            )
        prepared["_w"] = weights.fillna(0.0)
    else:
        prepared["_w"] = 1.0

    untreated_count = int(((prepared["_untreated"] == 1) & (prepared["_w"] > 0)).sum())
    if untreated_count == 0:
        raise ValidationError(
            "Untreated sample is empty (no never-treated units and no not-yet-treated periods with "
            "positive weight). Check Ei coding, weights, or extend the time window.",
        )

    # Panel balance diagnostics.
    periods_per_unit = prepared.groupby(id, sort=False)[time].nunique()
    is_balanced = bool(periods_per_unit.nunique() == 1)
    warnings: List[str] = []

    treated_subset = prepared.loc[prepared["_Ei_finite"]]
    if not treated_subset.empty:
        pre_period_mask = treated_subset[time] < treated_subset[Ei]
        pre_period_counts = (
            pre_period_mask.groupby(treated_subset[id], sort=False).sum().astype(int)
        )
        narrow_pre = sorted(
            [str(unit) for unit, count in pre_period_counts.items() if count < 2],
        )
        if narrow_pre:
            warnings.append(
                "Units with fewer than two pre-periods: "
                f"{narrow_pre[:5]}{'...' if len(narrow_pre) > 5 else ''}. "
                "Pretrend test may be unstable.",
            )

    cluster_col = cluster if cluster else id

    panel_meta: Dict[str, Any] = {
        "balanced": is_balanced,
        "n_units": int(prepared[id].nunique()),
        "n_periods_by_unit": {
            key: float(value) if isinstance(value, (np.floating, np.integer)) else value
            for key, value in periods_per_unit.describe().to_dict().items()
        },
        "warnings": warnings,
        "cluster": cluster_col,
    }

    return {"df": prepared, "panel_meta": panel_meta}
