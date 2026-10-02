import hashlib
import json
import pickle
from pathlib import Path

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def save_artifact(obj, filename, artifact_dir):
    filepath = Path(artifact_dir) / filename
    with open(filepath, "wb") as f:
        pickle.dump(obj, f)
    return compute_sha256(filepath)

def load_artifact(filename, artifact_dir, expected_hash=None):
    filepath = Path(artifact_dir) / filename
    if expected_hash:
        actual_hash = compute_sha256(filepath)
        if actual_hash != expected_hash:
            raise ValueError(f"Integrity check failed for {filename}. Expected {expected_hash}, got {actual_hash}.")
    
    with open(filepath, "rb") as f:
        return pickle.load(f)
