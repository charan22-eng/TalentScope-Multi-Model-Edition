# ADR-006: Conformal Prediction and Explainability

Status: Accepted

## Context
KNN provides deterministic distance-based predictions but lacks statistically rigorous confidence intervals. We need a way to say "The true label is in this set with 90% probability".

## Decision
- We use **Split-Conformal Prediction** with $\alpha=0.1$ to provide 90% coverage prediction sets.
- The threshold is calibrated strictly on the calibration set (20% of data) and is completely disjoint from the tuning process.
- We augment explainability with local counterfactuals over actionable features (e.g. `training_hours`) and a basic performance stability score (normalized entropy).

## Consequences
- The system can formally say "We are 90% sure this employee is either High or Medium".
- Some predictions may return an empty set or a set of 3 classes if the model is extremely uncertain.
- `calibration` partition must never be touched during parameter tuning.
