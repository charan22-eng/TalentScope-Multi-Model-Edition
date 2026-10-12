# TalentScope Multi-Model Edition: Senior Engineering Viva Q&A

This document compiles the foundational theoretical, statistical, architectural, and ethical questions for the TalentScope Multi-Model Edition defense and technical viva.

---

## 1. Statistical Comparison Science

### Q1: Why use paired stratified bootstrap rather than independent bootstrap resamples for confidence intervals?
**Answer**: Independent bootstrap resamples across two models introduce sample-to-sample variance that obscures the true difference between models. In a **paired** stratified bootstrap:
1. Every resample draws the exact same index set $S_b$ for both Model A and Model B.
2. For each replicate $b$, we compute the paired difference: $\Delta_b = \text{MacroF1}(A, S_b) - \text{MacroF1}(B, S_b)$.
3. Stratification ensures that the exact class proportions (Low/Medium/High) are preserved in every resample.
4. If the 95% bootstrap confidence interval of $\Delta_b$ contains zero, we cannot assert that Model A is statistically superior to Model B at $\alpha=0.05$. In our benchmark, the 95% difference CI between Random Forest and Boost is $[-0.012, +0.024]$, establishing that the champion's lead is **marginal** rather than statistically dominant.

### Q2: What is the McNemar test, and why was the Holm-Bonferroni correction necessary across 21 pairs?
**Answer**: 
- McNemar's test is a paired non-parametric test comparing the discordant predictions of two classifiers on the exact same test instances: $b$ (Model A wrong, Model B right) and $c$ (Model A right, Model B wrong).
- With $N=7$ models, evaluating all unique pairwise combinations yields $\binom{7}{2} = 21$ statistical hypothesis tests.
- Performing 21 unadjusted tests at $\alpha=0.05$ creates severe family-wise error inflation (probability of at least one false positive is $1 - (1-0.05)^{21} \approx 66\%$).
- Standard Bonferroni ($\alpha / 21$) is overly conservative and increases Type II error. The **Holm-Bonferroni step-down procedure** sorts raw p-values $p_{(1)} \le p_{(2)} \le \dots \le p_{(21)}$ and tests against $\alpha / (21 - k + 1)$, controlling the Family-Wise Error Rate (FWER) at 0.05 while retaining statistical power.

### Q3: How does Split-Conformal Prediction provide a mathematical guarantee?
**Answer**:
Conformal prediction transforms heuristic model probability distributions into set-valued predictions $C(X) \subseteq \{\text{Low}, \text{Medium}, \text{High}\}$ with a guaranteed finite-sample coverage property:
$$P(Y_{n+1} \in C(X_{n+1})) \ge 1 - \alpha$$
- We fit non-conformity scores $s_i = 1 - \hat{P}(Y_i \mid X_i)$ on a dedicated, holdout calibration set **cal-B** ($N=1,190$).
- We compute the quantile $\hat{q} = \text{Quantile}\left(\lceil (n+1)(1-\alpha) \rceil / n\right)$.
- At test time, $C(X) = \{y \in \mathcal{Y} \mid 1 - \hat{P}(y \mid X) \le \hat{q}\}$.
- This guarantee requires **no distributional assumptions** (non-parametric) and holds for any underlying model as long as test instances are exchangeable with calibration instances.

---

## 2. Multi-Criteria Champion Selection (ADR-009)

### Q4: SVM achieved the highest raw accuracy (81.6%). Why was Random Forest selected as the Champion over SVM?
**Answer**:
Under Multi-Criteria Decision Analysis (ADR-009), champion selection is governed by total composite utility across five standardized dimensions, rather than raw accuracy alone:
1. **Calibration (ECE)**: Random Forest achieved an Expected Calibration Error of $0.0133$, compared to SVM's $0.0270$. In HR decision support, well-calibrated probabilities are critical to prevent overconfident erroneous band placements.
2. **Explainability**: Random Forest provides native tree paths, Gini feature importances, and partial tree attributions. SVM with RBF kernel is a "black box" requiring surrogate kernel approximations.
3. **Inference Latency & Cost**: Random Forest single-row latency is $12.4\text{ ms}$, whereas RBF SVM dual-evaluation scales with support vectors.
4. Composite MCDA score under the **Balanced Profile** ranks Random Forest #1 with composite utility $0.842$, while SVM ranks #3 ($0.781$).

### Q5: What does the "Sensitivity Finding: No Model Dominates Everywhere" mean?
**Answer**:
By evaluating all 7 models across three distinct generator variants (`linear`, `nonlinear`, and `noisy_overlap`):
- In the `linear` data regime, **Linear Regression via ScoreToBand** achieved the highest rank-1 probability (99.8%) and superior macro-F1, outperforming complex ensembles due to zero parameter overfitting.
- In `nonlinear` and `noisy_overlap` regimes, tree ensembles (Random Forest, Gradient Boosting) dominate due to feature interaction capture.
- **Conclusion**: There is no universally superior machine learning model (consistent with the No Free Lunch Theorem). Model choice is fundamentally conditional on data structure.

---

## 3. Preprocessing, Leakage & Invariant Guards

### Q6: How is data leakage prevented between training, calibration, and test holdouts?
**Answer**:
Leakage is prevented via four cryptographic guards:
1. **Guard G4 (Model-Aware Preprocessing)**: The `build_preprocessor(spec)` factory fits scalers, imputers, and encoders **strictly on `X_train`**. Preprocessor transformations on `cal-A`, `cal-B`, and `test` call `.transform()` only. A continuous mutation script verifies that modifying holdout rows changes zero training parameters.
2. **Guard G5 (Frozen Disjoint Splits)**: The 60/10/10/20 split indices in `data/processed/split.json` are verified for mutual pairwise disjointness ($\text{train} \cap \text{cal-A} \cap \text{cal-B} \cap \text{test} = \emptyset$).
3. **Guard G6 (Cryptographic Test Lock)**: Test holdout data evaluation is strictly executed once under cryptographic configuration hash locking.

### Q7: Why is target `performance_score` and protected demographics excluded from features?
**Answer**:
1. `performance_score` is the continuous ground-truth target from which ordinal bands (`Low`, `Medium`, `High`) are derived. Including it would create 100% target leakage.
2. Protected attributes (`gender`, `age_band`, `ethnicity`) are separated into a dedicated table (`protected_attributes`) and barred from inference inputs by **Guard G2**. This ensures model decisions are driven exclusively by job-relevant operational factors (projects completed, attendance, peer feedback) in compliance with the TalentScope Ethics Charter.

---

## 4. Drift Monitoring & MLOps

### Q8: How is Population Stability Index (PSI) calculated and interpreted?
**Answer**:
PSI measures changes in the distribution of a continuous feature between a baseline reference dataset and current production data:
$$\text{PSI} = \sum_{k=1}^{B} \left( \text{Actual}_k - \text{Expected}_k \right) \times \ln\left( \frac{\text{Actual}_k}{\text{Expected}_k} \right)$$
- $\text{Expected}_k$: Percentage of baseline records falling in quantile bin $k$.
- $\text{Actual}_k$: Percentage of production records falling in quantile bin $k$.
- **Interpretation**:
  - $\text{PSI} < 0.10$: Stable; no significant distribution change.
  - $0.10 \le \text{PSI} < 0.25$: Moderate drift; warning triggered, schedule shadow monitoring.
  - $\text{PSI} \ge 0.25$: Significant distribution shift; retrain pipeline alert triggered.
- We augment PSI with the two-sample **Kolmogorov-Smirnov (KS) test** to detect cumulative distribution deviations.

### Q9: What is "Shadow Mode" in TalentScope?
**Answer**:
When an inference request is processed by the active champion (`rf`), the system concurrently executes runner-up model `boost` in background shadow mode:
- Both predictions are recorded in `predictions` table (`is_shadow=1` for boost).
- Disagreements between champion and shadow model are tracked in real-time.
- If shadow disagreement exceeds acceptable operational thresholds or champion stability degrades, the system surfaces candidate replacement telemetry for human administrator review.
