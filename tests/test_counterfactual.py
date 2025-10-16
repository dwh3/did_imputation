from __future__ import annotations

import numpy as np
import pandas as pd

from didimpute.counterfactual import compute_cell_effects
from didimpute.first_stage import FirstStageModel
from didimpute.validation import validate_and_prepare


def _tiny_panel() -> pd.DataFrame:
    """Return a minimal staggered-adoption panel with one never-treated cohort."""

    return pd.DataFrame(
        {
            "i": [1, 1, 1, 2, 2, 2, 3, 3, 3],
            "t": [0, 1, 2, 0, 1, 2, 0, 1, 2],
            "Ei": [2.0, 2.0, 2.0, 1.0, 1.0, 1.0, np.nan, np.nan, np.nan],
            "Y": [0.0, 0.1, 1.0, 0.2, 1.2, 2.2, 0.0, 0.0, 0.0],
        },
    )


def test_integration_up_to_counterfactuals() -> None:
    """Validate counterfactual shapes and masks on a small prepared panel."""

    ctx = validate_and_prepare(
        df=_tiny_panel(),
        y="Y",
        id="i",
        time="t",
        Ei="Ei",
        controls=None,
        weight=None,
        cluster=None,
    )
    prepared = ctx["df"]
    model = FirstStageModel().fit(
        df=prepared,
        y="Y",
        id="i",
        time="t",
        controls=None,
        weight=None,
    )
    cf = compute_cell_effects(
        df=prepared,
        y_col="Y",
        id_col="i",
        time_col="t",
        Ei_col="Ei",
        fsm=model,
        controls=None,
    )

    treated_mask = cf["masks"]["treated_post"]
    placebo_mask = cf["masks"]["treated_pre"]
    never_mask = cf["masks"]["never_treated"]

    assert len(cf["y0_hat"]) == len(prepared)
    assert np.isfinite(cf["y0_hat"]).all()
    assert np.all(np.isnan(cf["tau"][~treated_mask]))
    assert np.isfinite(cf["tau"][treated_mask]).all()
    assert np.all(np.isnan(cf["placebo"][~placebo_mask]))
    assert np.isfinite(cf["placebo"][placebo_mask]).all()
    assert never_mask.sum() == 3  # one unit, three periods
    np.testing.assert_array_equal(
        cf["masks"]["untreated_all"],
        prepared["_untreated"].to_numpy(dtype=bool),
    )
