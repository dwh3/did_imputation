# Parity Summary (Python ↔ Stata)

## Motivation

Imputation-based DID estimators provide unbiased event-study trajectories under staggered adoption when counterfactual outcomes are constructed from untreated cohorts. didimpute reproduces the workflow economists know from Stata while exposing a Pythonic API suitable for reproducible pipelines. To instill confidence that the port preserves the original estimator’s behavior, we validate against the canonical Stata implementation across seeded data-generating processes (DGPs).

## What “Parity” Means Here

- **Event-time estimates (`τ_k`)**: we align each treated event time `k` between Stata and Python outputs and compare point estimates.
- **Standard errors**: where Stata emits cluster-robust standard errors, we line them up and compute absolute deviations.
- **Pretrend diagnostics**: placebo effects for `k < 0` are tabulated so that the joint Wald tests agree in rejection behavior.
- **Coverage heuristics**: we report share of estimates within user-defined tolerances (default ≤0.05 absolute difference).

All comparisons run on deterministic CSV fixtures generated under seeds 100–149; the harness records raw tables plus summary statistics to `parity/out/`.

## Headline Results (latest manual run)

- `dgpB_const_te` (scheme=`nobs`, k=0..3): Share(|Δ estimate| ≤ 0.05) = 1.00; Max |Δ| = 0.0000
- `dgpB_const_te` (scheme=`equal`): 1.00
- `dgpB_const_te` (scheme=`cohort_share`): 1.00
- `dgpC_pretrend` (scheme=`nobs`, k=-3..0): 1.00
- `dgpA_no_treat`: no overlapping treated `k` rows (expected)

The full parity report lives at `parity/out/PARITY_REPORT.md`, alongside raw CSV tables for transparency.

## Interpreting the Report

1. **Share(|Δ estimate| ≤ ε)** close to 1.0 indicates the estimator matches Stata within tolerance `ε`; investigate outliers when the share drops.
2. **Max |Δ|** highlights worst-case deviations. Non-zero values typically signal insufficient support or failing first-stage assumptions.
3. **Pretrend rows**: when Stata lacks overlapping negative event-times, the Python harness marks the test as “not run” to avoid false alarms.
4. **Missing rows**: if Stata omits certain `k` (e.g., no treated observations), expect `nan`/missing entries; didimpute mirrors that behavior by design.

When extending the estimator or adding weight schemes, update the parity harness to cover new scenarios and re-freeze the golden regression outputs in `tests/golden/`.

## Regression Guardrails

- Python goldens for canonical scenarios live in `tests/golden/`.
- CI enforces parity by comparing fresh summaries to these goldens with tight tolerances (1e-6 absolute on estimates/SEs).
- Stata is *optional*: the parity harness can be run manually when Stata is available; CI depends only on the goldens.
