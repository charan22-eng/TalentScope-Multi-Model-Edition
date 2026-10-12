# ADR-007: Preprocessing Policy for the Seven-Model Arena

## Status
Accepted

## Date
2026-10-12

## Context
TalentScope Multi-Model Edition evaluates seven distinct algorithms on an ordered three-class performance prediction task. The candidate models span three broad families:
1. Linear/Margin/Distance models (`linreg`, `logreg`, `knn`, `svm`)
2. Decision trees and tree ensembles (`dt`, `rf`, `boost`)

Comparing models fairly requires a single, leakage-safe preprocessing factory that does not disadvantage models with specific scaling needs, nor burden tree architectures with unnecessary monotonic transformations.

## Decisions
1. **Model-Aware Scaling**:
   - Algorithms sensitive to feature scale (`linreg`, `logreg`, `knn`, `svm`) receive `StandardScaler` (zero mean, unit variance).
   - Algorithms invariant to monotonic scaling (`dt`, `rf`, `boost`) receive `passthrough` (no scaler), preserving natural threshold semantics and minimizing pipeline latency.
2. **Missing Data Imputation**:
   - `SimpleImputer(strategy="median")` is fitted on training numerics. This satisfies the 3%–5% missingness realism layer without creating cross-fold leakage.
3. **Outlier Mitigation**:
   - Outliers are clipped via `Winsorizer(lower=0.01, upper=0.99)` with bounds learned strictly from training folds (G4 invariant).
4. **Categorical & Ordinal Encoding**:
   - `department` (8 categories) is encoded via `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`.
   - `job_level` has a natural hierarchy and is encoded via `OrdinalEncoder` mapping `Junior`=0, `Mid`=1, `Senior`=2, `Lead`=3.
5. **Label Ordering**:
   - Target bands are encoded strictly as ordered integers: `Low`=0, `Medium`=1, `High`=2. Alphabetical ordering (`High`=0, `Low`=1, `Medium`=2) is forbidden across the codebase to prevent corrupted probability matrices and ordinal metrics.
6. **Ablation Findings (5-Fold Stratified CV on Dataset v2)**:
   - Logistic Regression: Winsor ON = 0.7076 ± 0.0056, Winsor OFF = 0.7093 ± 0.0060 (delta < 0.002; Winsorizing retained for tail robustness).
   - Random Forest: Winsor ON = 0.7723 ± 0.0077, Winsor OFF = 0.7733 ± 0.0061 (tree splits remain robust; Winsorizing retained for unified pipeline safety).

## Consequences
- Guaranteed zero data leakage across all 7 model specifications (G4 invariant passing).
- Reproducible, model-appropriate feature representation across all downstream training sessions.
