# SPEC — Behavioral Matrix (v0.1)
**Input columns**
- outcome: y; unit: id; time: t (integer-castable); adoption time: Ei (NaN => never-treated)
- optional: controls X[], weight w>=0, cluster id (defaults to id)

**Estimator steps**
1) Untreated sample = never-treated OR not-yet-treated (t < Ei).
2) Two-way FE on untreated sample: y ~ controls + α_i + λ_t (WLS if weights).
3) Predict counterfactual for all cells with observed (i,t) labels from untreated sample; compute:
   - treated-post cells: τ_it = y_it - ŷ^0_it
   - eventual-treated pre-periods: placebo for pretrend test
4) Aggregate τ_it to event-time k = t - Ei with selected weights.
5) Cluster-robust SEs by id for each k; joint pretrend test over k<0.

**Aggregation weights (per event-time k)**
- nobs: equal weight per cell (simple mean across treated cells at k).
- equal: equal weight per cohort (cohort = Ei); average cohort means at k equally.
- cohort_share: weight cohort means by cohort share at k (n_{g,k}/N_k).

**CLI**
- didimpute --csv ... --y Y --id i --time t --Ei Ei [--cluster id --controls X1,X2 --weight w --horizons -5:10 --pretrends 5 --scheme equal|nobs|cohort_share]

**Limitations v0.1**
- Single adoption event; no wild bootstrap; one-way clustering; no missing-data strategies beyond listwise.
