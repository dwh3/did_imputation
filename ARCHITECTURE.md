# ARCHITECTURE
Pipeline:
validate_and_prepare -> FirstStageModel.fit -> compute_cell_effects -> aggregate_event_time
-> attach_ses_by_k + finalize_summary_ci -> pretrend_joint_test -> Result

Errors:
- ValidationError: schema, types, duplicates, invalid horizons/minN, empty untreated, unknown labels at prediction.
- EstimationError: rank deficiency, singular design, no positive-weight untreated, prediction with unseen id/time.
