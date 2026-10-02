# Model Card: Employee Performance Intelligence (KNN)

## Model Details
- **Architecture**: K-Nearest Neighbors (k=5) + Sigmoid Calibration
- **Version**: v1.0 (v0.5.1 Phase 5)
- **Date**: October 2026
- **License**: Internal Use Only

## Intended Use
- **Primary Use Case**: Decision-support tool for HR managers and Team Leads to review employee performance.
- **Out of Scope**: Fully automated promotions, firings, or compensation adjustments.

## Factors
- **Demographics**: Explicit demographic features (race, gender, age) were excluded.
- **Proxies**: `department` and `job_level` are evaluated for proxy bias.

## Metrics (from artifacts/v1/metadata.json)
- **CV Macro F1 (5x3)**: 0.655
- **Test Macro F1**: 0.662
- **Exact Match Rate**: 65.7%
- **Adjacent Error Rate**: 33.4%
- **Extreme Error Rate**: 0.9%
- **Calibrated Brier Score**: 0.121

## Evaluation Data
- **Test Split**: 20% (Disjoint from Train 60% and Calib 20%).
- **Robustness**: Model drops less than 5% exact-match stability under 10% Gaussian noise injection.

## Mitigation Lab (Experimental)
> **WARNING**: The mitigation modules (e.g. `bias_injection_test`) are strictly experimental sandboxes and are NOT deployed in the active prediction pipeline.

## Ethical Considerations
Synthetic data inherently fails to capture intersectional nuance. The prediction sets (90% Conformal Coverage) ensure uncertainty is communicated transparently.
