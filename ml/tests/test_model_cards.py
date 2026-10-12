"""Test model card parity against machine JSON files (VM7.5)."""

import json
from pathlib import Path
import pytest

from epk.models.registry import MODEL_KEYS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
V2_DIR = REPO_ROOT / "artifacts" / "v2"
DOCS_DIR = REPO_ROOT / "docs"
CARDS_DIR = DOCS_DIR / "model_cards"


@pytest.mark.parametrize("model_key", sorted(list(MODEL_KEYS)))
def test_model_card_numbers_match_json(model_key):
    """Verify that numbers cited in model card match metrics.json exactly."""
    card_path = CARDS_DIR / f"{model_key}.md"
    assert card_path.exists(), f"Model card missing: {card_path}"

    metrics_path = V2_DIR / "models" / model_key / "metrics.json"
    assert metrics_path.exists(), f"Metrics file missing: {metrics_path}"

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    card_text = card_path.read_text(encoding="utf-8")

    # Check macro-F1
    macro_f1_str = f"`{metrics['macro_f1']:.4f}`"
    assert macro_f1_str in card_text, f"Macro-F1 {macro_f1_str} not found in {card_path.name}"

    # Check Accuracy
    acc_str = f"`{metrics['accuracy']:.4f}`"
    assert acc_str in card_text, f"Accuracy {acc_str} not found in {card_path.name}"

    # Check synthetic caveat
    assert "Rankings depend on the synthetic generator" in card_text


def test_comparison_model_card_exists():
    """Verify comparison card exists and contains champion and caveat."""
    card_path = DOCS_DIR / "model_card.md"
    assert card_path.exists()
    content = card_path.read_text(encoding="utf-8")
    assert "Random Forest" in content
    assert "Rankings depend on the synthetic generator" in content


def test_datasheet_v2_exists():
    """Verify datasheet exists and contains 12,000-row volume and 3 variants."""
    ds_path = DOCS_DIR / "datasheet.md"
    assert ds_path.exists()
    content = ds_path.read_text(encoding="utf-8")
    assert "11904" in content or "11,904" in content
    assert "nonlinear" in content
    assert "linear" in content
    assert "noisy_overlap" in content
