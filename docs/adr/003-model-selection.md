# ADR-003: Model Selection

Status: Accepted
Date: 2026-09-29

## Context
We need to select the primary classification model for predicting employee performance bands. The choices evaluated included Logistic Regression, Random Forest, Gradient Boosting, and a tuned K-Nearest Neighbors (KNN).

## Options
1. **Gradient Boosting / Random Forest:** Highest predictive accuracy (F1), but lack inherent local explainability without complex post-hoc explainers like SHAP, which can be unintuitive for non-technical HR personnel.
2. **Logistic Regression:** Good baseline, interpretable globally (coefficients), but strictly linear.
3. **K-Nearest Neighbors (KNN):** Slightly lower predictive F1 than tree ensembles, but offers a unique, fully transparent explanation by retrieving the actual most similar past employees (the "neighbours").

## Decision
We chose **KNN (Tuned)** as the primary model. While tree-based ensembles may score slightly higher on raw accuracy metrics, the primary differentiator of this product is *explainability*. Being able to show a reviewer exactly *which* past employees form the basis of the prediction provides a level of trust and intuitiveness that complex post-hoc explanations cannot match. We will retain the strongest challenger model (e.g. Gradient Boosting) purely as a "second opinion" benchmark displayed in the Model Lab.

## Consequences
- Requires careful handling of latency at scale, as KNN prediction time grows with the training set size (O(Nd)).
- We must maintain the training dataset in memory (or via efficient search indexes like KD-Tree/Ball-Tree).
