"""update_model_cards_confirmation.py — Update model cards with confirmation run section.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "reports" / "confirmation_evaluation.json", "r") as f:
    conf = json.load(f)

models_data = conf["models"]
mcda_data = conf["mcda_profiles"]

# 1. Update docs/model_card.md
model_card_path = ROOT / "docs" / "model_card.md"
with open(model_card_path, "r", encoding="utf-8") as f:
    mc_content = f.read()

# Only append if not already present
if "## 6. Fresh-Seed Confirmation Run" not in mc_content:
    conf_section = """

## 6. Fresh-Seed Confirmation Run (Seed = 2026, N = 2,381)
> [!NOTE]
> **Strictly Observational**: Per FF4 Item 3, this fresh-seed confirmation run evaluates all final models and calibrators on an independent, unseen synthetic draw (seed 2026, non-linear variant, 11,904 rows, test N = 2,381). **Zero retraining or hyperparameter tuning was performed.** Confirmation data was never used for model choice.

### Confirmation Holdout Metrics (N = 2,381, Seed = 2026)
| Rank | Model | Family | Macro-F1 (95% CI) | Accuracy (95% CI) | QWK (95% CI) | ECE | Conformal Cov. (α=0.10) |
|---|---|---|---|---|---|---|---|
| 1 | **Support vector machine (RBF)** (`svm`) | Kernel | `0.7997` [0.7831, 0.8157] | `0.7992` [0.7833, 0.8152] | `0.8037` [0.7853, 0.8209] | `0.0055` | `0.2831` |
| 2 | **Gradient boosting (histogram)** (`boost`) | Ensemble | `0.7937` [0.7772, 0.8100] | `0.7904` [0.7740, 0.8068] | `0.7943` [0.7757, 0.8121] | `0.0160` | `0.2801` |
| 3 | **Random forest** (`rf`) | Ensemble | `0.7638` [0.7466, 0.7806] | `0.7610` [0.7438, 0.7778] | `0.7645` [0.7447, 0.7832] | `0.0197` | `0.2394` |
| 4 | **Logistic regression (multinomial)** (`logreg`) | Linear | `0.7107` [0.6923, 0.7289] | `0.7098` [0.6917, 0.7283] | `0.7011` [0.6788, 0.7225] | `0.0270` | `0.0932` |
| 5 | **K-nearest neighbours** (`knn`) | Instance | `0.7058` [0.6872, 0.7243] | `0.7144` [0.6963, 0.7329] | `0.6865` [0.6635, 0.7088] | `0.0276` | `0.1243` |
| 6 | **Decision tree** (`dt`) | Tree | `0.6914` [0.6728, 0.7099] | `0.6926` [0.6737, 0.7106] | `0.6670` [0.6433, 0.6896] | `0.0268` | `0.0701` |
| 7 | **Linear regression (score to band)** (`linreg`) | Linear | `0.6873` [0.6684, 0.7058] | `0.6867` [0.6678, 0.7052] | `0.6756` [0.6521, 0.6978] | `0.0381` | `0.0811` |

### Confirmation MCDA Ranking (Seed = 2026)
- **Balanced**: Winner = `boost` (0.8114) vs Runner-up = `rf` (0.6637) | `svm` (0.6582, rank 3) | Rank-1 Prob = 99.9% | Decision Strength = `marginal`
- **Accuracy-first**: Winner = `boost` (0.9557) vs `svm` (0.8282) | Rank-1 Prob = 100.0% | Strength = `marginal`
- **Explainability-first**: Winner = `logreg` (0.7037) vs `boost` (0.6971) | Rank-1 Prob = 56.7% | Strength = `none`
- **Speed-first**: Winner = `boost` (0.4700) vs `svm` (0.3917) | Rank-1 Prob = 99.9% | Strength = `marginal`
- **Fairness-first**: Winner = `boost` (0.8686) vs `rf` (0.7529) | Rank-1 Prob = 100.0% | Strength = `marginal`
"""
    with open(model_card_path, "w", encoding="utf-8") as f:
        f.write(mc_content.rstrip() + conf_section)
    print("Updated docs/model_card.md")

# 2. Update docs/model_cards/<model>.md
for m_key, m_info in models_data.items():
    card_path = ROOT / "docs" / "model_cards" / f"{m_key}.md"
    if not card_path.exists():
        continue
    with open(card_path, "r", encoding="utf-8") as f:
        c_text = f.read()

    if "## 7. Fresh-Seed Confirmation Run" not in c_text:
        acc = m_info["accuracy"]
        acc_ci = m_info["accuracy_ci"]
        f1 = m_info["macro_f1"]
        f1_ci = m_info["macro_f1_ci"]
        qwk = m_info["qwk"]
        qwk_ci = m_info["qwk_ci"]
        ece = m_info["ece"]
        cov = m_info["conformal_coverage"]
        sz = m_info["conformal_mean_set_size"]

        single_section = f"""

## 7. Fresh-Seed Confirmation Run (Seed = 2026, N = 2,381)
> [!NOTE]
> **Strictly Observational**: Evaluated frozen on seed 2026 (variant: non-linear, test N = 2,381) with zero retraining or hyperparameter tuning. Never used for model choice.

- **Accuracy**: `{acc:.4f}` (95% CI: [{acc_ci[0]:.4f}, {acc_ci[1]:.4f}])
- **Macro-F1**: `{f1:.4f}` (95% CI: [{f1_ci[0]:.4f}, {f1_ci[1]:.4f}])
- **Quadratic Weighted Kappa (QWK)**: `{qwk:.4f}` (95% CI: [{qwk_ci[0]:.4f}, {qwk_ci[1]:.4f}])
- **Expected Calibration Error (ECE)**: `{ece:.4f}`
- **Conformal Coverage (α = 0.10)**: `{cov*100:.1f}%` (Mean set size: `{sz:.2f}`)
"""
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(c_text.rstrip() + single_section)
        print(f"Updated docs/model_cards/{m_key}.md")
