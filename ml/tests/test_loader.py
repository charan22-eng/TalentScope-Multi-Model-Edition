import pytest
import pickle
from pathlib import Path
from epk.loader import load_artifact, compute_sha256

def test_loader_integrity(tmp_path):
    artifact_path = tmp_path / "test.pkl"
    with open(artifact_path, "wb") as f:
        pickle.dump({"a": 1}, f)
        
    true_hash = compute_sha256(artifact_path)
    
    # Valid hash should load
    obj = load_artifact("test.pkl", tmp_path, expected_hash=true_hash)
    assert obj == {"a": 1}
    
    # Invalid hash should raise
    with pytest.raises(ValueError):
        load_artifact("test.pkl", tmp_path, expected_hash="bad_hash")
