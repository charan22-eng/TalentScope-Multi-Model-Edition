# Ethics and Scope Charter

## Intended Use
This model is designed solely as a **decision support tool** for HR professionals and team leads. It provides a data-driven "second opinion" on an employee's performance band, accompanied by explainable metrics (nearest neighbours, feature attribution) to foster transparency.

## Out-of-Scope Use
- **Automated decisions:** The model must **never** be used to automatically hire, fire, promote, or demote an employee without human intervention.
- **Profiling:** The model should not be used to profile employees based on protected attributes.

## Fairness and Bias
- Protected attributes (e.g., gender, age_band) are strictly excluded from the training features.
- The system includes a fairness audit module (Phase 9) to monitor disparity ratios and proxy variables.
- Any prediction with low confidence or high disagreement with baselines is flagged for mandatory human review.
