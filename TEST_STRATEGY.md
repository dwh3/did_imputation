# TEST_STRATEGY
**Determinism:** explicit seeds; random_state reserved (no RNG in v0.1).
**DGPs and tolerances (50 sims over seeds 100..149):**
- Constant-TE: n_i=60, T=10, te=1.0, sigma=0.1 -> for k in [0,3], |mean(est - 1.0)| < 0.05; 95% CI coverage in [0.93, 0.97]
- No-treat: for k in [-3,3], mean |est| < 0.05
- Pretrend slope=0.10 sd/period: pretrend joint test (α=0.05) rejects in ≥ 80% of sims
**Unit tests:** schema, validation, first-stage rank deficiency, aggregation weights, SEs, plotting.
Validation: duplicates, horizons/minN, weights, pre-period warnings recorded in meta.
