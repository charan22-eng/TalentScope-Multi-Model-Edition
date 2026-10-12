import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

ROOT = Path(".")

def test_x20_knn_by_hand():
    print("--- X20 KNN Neighbours By Hand ---")
    # Load KNN artifact
    knn_dir = ROOT / "artifacts/v2/models/knn"
    if not knn_dir.exists():
        print("[FAIL] Missing artifacts/v2/models/knn")
        return False
        
    # Read test predictions to find a test sample
    df_test = pd.read_csv(knn_dir / "test_predictions.csv")
    first_row_idx = int(df_test.iloc[0]["row_index"])
    
    # Read clean dataset and split
    clean_df = pd.read_csv(ROOT / "data/nonlinear/dataset.csv")
    with open(ROOT / "data/processed/split.json", "r", encoding="utf-8") as f:
        split = json.load(f)
        
    train_indices = split["train_indices"]
    feature_cols = [
        "attendance", "experience_years", "training_hours", "projects_completed",
        "weekly_hours", "prev_score", "peer_feedback", "tasks_on_time_pct", "certifications"
    ]
    
    X_num = clean_df[feature_cols].fillna(clean_df[feature_cols].median()).values
    X_train = X_num[train_indices]
    x_query = X_num[first_row_idx].reshape(1, -1)
    
    # Hand calculation: Euclidean distance
    # d(x, y) = sqrt(sum((x_i - y_i)^2))
    diffs = X_train - x_query
    dists_hand = np.sqrt(np.sum(diffs ** 2, axis=1))
    nearest_hand_idx = np.argsort(dists_hand)[:5]
    nearest_hand_dists = dists_hand[nearest_hand_idx]
    
    # Compare with sklearn NearestNeighbors
    nn = NearestNeighbors(n_neighbors=5, metric="euclidean")
    nn.fit(X_train)
    dists_sk, idx_sk = nn.kneighbors(x_query)
    
    dists_match = np.allclose(nearest_hand_dists, dists_sk[0], atol=1e-6)
    idx_match = np.array_equal(nearest_hand_idx, idx_sk[0])
    passed = dists_match and idx_match
    print(f"Hand dists   : {nearest_hand_dists[:3]}")
    print(f"Sklearn dists: {dists_sk[0][:3]}")
    print(f"[X20 KNN by hand]: {'PASS' if passed else 'FAIL'}")
    return passed

def test_x21_surface_cells():
    print("\n--- X21 Surface Cells Verification ---")
    surf_file = ROOT / "artifacts/v2/explainability/surfaces.json"
    if not surf_file.exists():
        print(f"[FAIL] Missing {surf_file}")
        return False
        
    with open(surf_file, "r", encoding="utf-8") as f:
        grids = json.load(f)
        
    print(f"Surface grids loaded with models: {list(grids.keys())}")
    for k in list(grids.keys()):
        grid = grids[k]
        size = grid.get("grid_size", 0)
        preds = grid.get("grid_predictions", [])
        assert size == 40, f"Expected 40x40, got size {size}"
        preds_arr = np.array(preds)
        assert preds_arr.shape == (40, 40), f"Expected (40, 40), got shape {preds_arr.shape}"
        assert set(np.unique(preds_arr)).issubset({0, 1, 2}), f"Unexpected classes: {np.unique(preds_arr)}"
        print(f"[PASS] Model {k:7s} 40x40 grid (1,600 cells) verified with valid bands: {np.unique(preds_arr)}")
    return True

if __name__ == "__main__":
    r20 = test_x20_knn_by_hand()
    r21 = test_x21_surface_cells()
    exit(0 if (r20 and r21) else 1)
