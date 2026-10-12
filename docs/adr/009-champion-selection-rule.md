# ADR-009: Champion Selection Rule and Multi-Criteria Decision Analysis (MCDA)

## Status
Accepted

## Context
TalentScope compares seven diverse algorithms (linear regression via ScoreToBand, logistic regression, KNN, SVM, decision tree, random forest, and gradient boosting) across multiple competing dimensions: predictive accuracy (macro-F1, QWK), probability calibration (1 - ECE), robustness against noise and missingness, fairness disparity, stability across random seeds, inference latency, training cost, and explainability tier.
No single model dominates on every dimension: for example, SVM achieves superior accuracy but has higher latency than a decision tree; gradient boosting achieves high macro-F1 but decision trees offer native white-box rules.

To eliminate subjective champion selection and guarantee that algorithmic recommendations are mathematically sound and verifiable by code, we require a deterministic, auditable multi-criteria decision framework.

## Decision

### 1. Multi-Criteria Decision Analysis (MCDA) Engine
We implement an additive weighted-sum MCDA with min-max normalization across 9 criteria:
- **Higher is better**: `macro_f1`, `qwk`, `calibration` ($1 - \text{ECE}$), `robustness` ($1 - \text{drop}$), `fairness` (disparity ratio), `stability` ($1 - \text{std}$), `explainability` (rubric: native 1.0, partial 0.6, post-hoc 0.3).
- **Lower is better**: `latency` (single-row p95 ms), `train_cost` (tuning time seconds).

### 2. Five Priority Profiles
1. **Balanced** (Default): macro-F1 (0.30), explainability (0.15), QWK (0.10), calibration (0.10), robustness (0.10), fairness (0.10), stability (0.05), latency (0.05), train_cost (0.05).
2. **Accuracy-first**: macro-F1 (0.50), QWK (0.15), calibration (0.10), robustness (0.10), fairness (0.05), stability (0.05), latency (0.02), train_cost (0.01), explainability (0.02).
3. **Explainability-first**: explainability (0.35), macro-F1 (0.20), calibration (0.10), fairness (0.10), QWK (0.05), robustness (0.05), stability (0.05), latency (0.05), train_cost (0.05).
4. **Speed-first**: latency (0.30), train_cost (0.20), macro-F1 (0.20), QWK (0.05), calibration (0.05), robustness (0.05), fairness (0.05), stability (0.05), explainability (0.05).
5. **Fairness-first**: fairness (0.35), macro-F1 (0.20), calibration (0.10), robustness (0.10), QWK (0.05), stability (0.05), latency (0.05), train_cost (0.05), explainability (0.05).

Users on the website can adjust weights via interactive sliders; the backend recomputes scores dynamically using the identical mathematical engine.

### 3. Rank Probability via Dirichlet Perturbation
To quantify sensitivity to weight choices, we draw $N = 5,000$ weight vectors from a Dirichlet distribution:
$$\mathbf{w}^{(draw)} \sim \text{Dirichlet}(\alpha = 50 \cdot \mathbf{w}_{\text{base}})$$
The share of draws in which each model achieves rank 1 is its rank-1 probability ($p_{\text{rank1}}$).

### 4. Decision Strength Determination
A model is deemed the champion only with an explicit decision strength badge:
- **Clear**: ALL THREE conditions hold:
  1. The 95% paired stratified bootstrap difference interval of macro-F1 between rank 1 and rank 2 strictly excludes zero ($\text{CI}_{\text{lower}} > 0$).
  2. The pairwise McNemar test with Holm-Bonferroni correction between rank 1 and rank 2 has $p_{\text{adj}} < 0.05$.
  3. The Dirichlet rank-1 probability $p_{\text{rank1}} \ge 0.80$.
- **Marginal**: At least one, but not all three conditions hold (models are separated on some criteria but without decisive statistical dominance).
- **None**: None of the conditions hold (a statistical tie or ambiguous trade-off).

### 5. Architectural Rule: Code Decides, LLM Narrates
The deterministic winner and decision strength are computed exclusively by code. The LLM verdict engine is forbidden from changing the winner or asserting "clear" confidence when the decision strength is marginal or none.

## Consequences
- Guaranteed mathematical reproducibility: rankings are computed from machine JSON files without human bias.
- Transparent trade-off communication for non-technical HR users and deep-learning auditors.
- Explicit uncertainty guarding against overclaiming model superiority.
