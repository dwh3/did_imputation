from __future__ import annotations

import numpy as np
import pandas as pd

from didimpute import DidImputation

from .dgp import dgp_constant_te, dgp_no_treat, dgp_pretrend

SEEDS = list(range(100, 150))  # 50 simulations


def _run_constant_te_once(seed: int) -> tuple[float, float, float, float]:
    df = dgp_constant_te(seed=seed)
    result = DidImputation(y="Y", id="i", time="t", Ei="Ei", horizons=(0, 3), minN=1).fit(df)
    summary = result.summary()
    post = summary[(summary["k"] >= 0) & (summary["k"] <= 3)]
    mean_est = float(post["estimate"].mean())
    mean_se = float(post["se"].mean())
    ci_low_ok = float((post["ci_low"] <= 1.0).mean())
    ci_high_ok = float((post["ci_high"] >= 1.0).mean())
    return mean_est, mean_se, ci_low_ok, ci_high_ok


def test_constant_te_bias_and_coverage() -> None:
    """Constant treatment effects should be unbiased with nominal coverage."""

    estimates = []
    coverage_flags = []
    for seed in SEEDS:
        mean_est, _mean_se, low_ok, high_ok = _run_constant_te_once(seed)
        estimates.append(mean_est)
        coverage_flags.append(1.0 if (low_ok == 1.0 and high_ok == 1.0) else 0.0)
    bias = abs(np.mean(estimates) - 1.0)
    coverage = np.mean(coverage_flags)
    assert bias < 0.05
    assert 0.93 <= coverage <= 0.97


def test_no_treat_near_zero() -> None:
    """Without treatment the estimator should be centered near zero."""

    values = []
    for seed in SEEDS[:20]:
        df = dgp_no_treat(seed=seed)
        result = DidImputation(y="Y", id="i", time="t", Ei="Ei", horizons=(-3, 3), minN=1).fit(df)
        summary = result.summary()
        window = summary[(summary["k"] >= -3) & (summary["k"] <= 3)]
        if window.empty:
            values.append(0.0)
        else:
            values.append(float(window["estimate"].abs().mean()))
    assert np.mean(values) < 0.05


def test_pretrend_rejection_rate() -> None:
    """Pretrend test should reject when treated units drift before adoption."""

    rejections = []
    for seed in SEEDS:
        df = dgp_pretrend(seed=seed, pre_slope=0.10)
        result = DidImputation(
            y="Y",
            id="i",
            time="t",
            Ei="Ei",
            pretrends=3,
            horizons=(-3, 3),
            minN=1,
        ).fit(df)
        pvalue = result.meta["pretrend"]["pvalue"]
        rejections.append(1.0 if (pd.notna(pvalue) and pvalue < 0.05) else 0.0)
    assert np.mean(rejections) >= 0.80
