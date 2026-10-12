"""Legacy train entrypoint for TalentScope.

Delegates to epk.train_all for fair multi-model training and calibration.
The held-out test split is evaluated strictly once via make final (epk.final_eval).
"""

import sys
from pathlib import Path

# Ensure ml/src is on sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from epk.train_all import run_training_pipeline


def main():
    profile = "fast"
    if "--profile" in sys.argv:
        idx = sys.argv.index("--profile")
        if idx + 1 < len(sys.argv):
            profile = sys.argv[idx + 1]
    run_training_pipeline(profile=profile)


if __name__ == "__main__":
    main()
