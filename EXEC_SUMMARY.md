# didimpute — Executive Summary
Goal: Audit-ready Python re-implementation of imputation-based DID (staggered adoption).
Scope: v0.1 covers API/CLI, core estimator, SEs, pretrend, plotting, parity harness.
Risks: Spec drift; rank deficiency; sparse cohorts.
Mitigations: Numeric parity tolerances; strict validation; robust dummy path.
Status: Planning finalized with explicit tolerances (see TEST_STRATEGY).

Status: Core pipeline implemented; docs updated with interpretation guidance.
