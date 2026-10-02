# Problem Statement & Specification

## Objective
Predict an employee's performance band based on their work metrics, providing clear explanations to support HR decision-making. 

## Inputs
Core features (attendance, experience, training, projects, weekly hours, prior score) and categorical features (department, job_level). Protected attributes (gender, age_band) are strictly for auditing.

## Output
An ordered class prediction: `Low` < `Medium` < `High`.

## Success Metrics
- **Model quality:** Cross-validated macro-F1 >= 0.80.
- **Error bounds:** Extreme errors (predicting Low when actual is High, or vice versa) <= 3%.
- **Baselines:** The tuned KNN must clearly outperform majority-class guessing and unscaled KNN.
- **API Latency:** Single prediction p95 < 300 ms; 5,000-row batch < 10 s.
- **UX & Accessibility:** Lighthouse score >= 90; SUS score >= 75.

## Non-goals
- We will not automate hiring or firing decisions. This is a decision-support tool.
- We are not predicting future potential, only classifying the current-period performance composite.

## Baseline Hypotheses
1. Higher project count and higher prior score increase the probability of a `High` performance classification.
2. Low attendance combined with low training hours correlates with `Low` performance.
3. Experience years have a non-linear relationship (diminishing returns) with performance.
