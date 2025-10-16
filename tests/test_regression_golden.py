import numpy as np
import pandas as pd

from didimpute import DidImputation

TOL_EST = 1e-6
TOL_SE = 1e-6

def _cmp(golden_path: str, in_path: str, horizons, scheme: str) -> None:
    golden = pd.read_csv(golden_path).rename(columns=str.lower)
    df = pd.read_csv(in_path)
    result = DidImputation(
        y="Y",
        id="i",
        time="t",
        Ei="Ei",
        horizons=horizons,
        weight_scheme=scheme,
        minN=1,
    ).fit(df)
    summary = result.summary().rename(columns=str.lower)

    if golden.empty:
        assert summary.empty, "Expected empty summary for golden with no rows"
        return

    merged = pd.merge(summary, golden, on="k", suffixes=("_cur", "_gold"), how="inner")
    assert len(merged) == len(golden), "Golden and current have different k rows"

    if {"estimate_cur", "estimate_gold"}.issubset(merged.columns):
        assert np.allclose(
            merged["estimate_cur"],
            merged["estimate_gold"],
            atol=TOL_EST,
            rtol=0.0,
        ), merged[["k", "estimate_cur", "estimate_gold"]]

    if {"se_cur", "se_gold"}.issubset(merged.columns):
        mask = np.isfinite(merged["se_cur"]) & np.isfinite(merged["se_gold"])
        if mask.any():
            assert np.allclose(
                merged.loc[mask, "se_cur"],
                merged.loc[mask, "se_gold"],
                atol=TOL_SE,
                rtol=0.0,
            ), merged.loc[mask, ["k", "se_cur", "se_gold"]]

def test_golden_const_te_nobs() -> None:
    _cmp(
        "tests/golden/dgpB_const_te_py_nobs_0_3.csv",
        "parity/out/dgpB_const_te.csv",
        (0, 3),
        "nobs",
    )

def test_golden_const_te_equal() -> None:
    _cmp(
        "tests/golden/dgpB_const_te_py_equal_0_3.csv",
        "parity/out/dgpB_const_te.csv",
        (0, 3),
        "equal",
    )

def test_golden_no_treat_nobs() -> None:
    _cmp(
        "tests/golden/dgpA_no_treat_py_nobs_-3_3.csv",
        "parity/out/dgpA_no_treat.csv",
        (-3, 3),
        "nobs",
    )
