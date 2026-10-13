# ADR-011: Artifact Storage and Distribution Strategy for Multi-Model Deliverables

## Status
Accepted

## Date
2026-10-13

## Context
The TalentScope v2 multi-model release produces trained model pipelines, calibrated prediction sets, explainability surfaces, and comparison metrics for seven diverse architectures (`linreg`, `logreg`, `dt`, `rf`, `boost`, `svm`, `knn`).

An audit of the on-disk footprint under `artifacts/` reveals:
- **Total Payload Size**: 30.24 MB across 54 tracked files.
- **Size Distribution**:
  - `artifacts/v2/models/rf/model.joblib`: 26.09 MB (largest file; ensemble of 100 deep trees).
  - `artifacts/v2/models/boost/model.joblib`: 1.03 MB (LightGBM/HistGradientBoosting).
  - `artifacts/v2/models/knn/model.joblib`: 1.01 MB (k-Nearest Neighbors tree index).
  - `artifacts/v2/models/svm/model.joblib`: 0.75 MB (RBF Support Vector Classifier support vectors).
  - `artifacts/v2/models/dt/model.joblib`: 0.05 MB.
  - `artifacts/v2/models/logreg/model.joblib`: 0.02 MB.
  - `artifacts/v2/models/linreg/model.joblib`: 0.02 MB.
  - Decision surfaces, PCA coordinates, test predictions, and split files: ~1.27 MB combined.

Three options were evaluated for managing these artifacts across clones, CI, and deployment environments:
1. **Direct Git Commit with Cryptographic Manifest**: Keep `artifacts/v2/` committed directly to the git repository (whitelisted via `!artifacts/v2/` in `.gitignore`), protected by `artifacts/v2/MANIFEST.json` SHA-256 hashes and Guard G8.
2. **Git LFS (Large File Storage)**: Track `*.joblib` binary artifacts via Git LFS pointers with external blob hosting.
3. **Ephemeral Rebuild (`make train` on clone)**: Exclude model binaries from version control entirely and require consumers/CI to run `make train` upon clone.

## Options Analysis

### Option 1: Direct Git Commit (Selected)
- **Pros**:
  - Completely self-contained repository: zero external dependencies, no Git LFS server required, no credential configuration needed for external object stores.
  - Air-gapped and offline reproducible: verification scripts (`make verify`, `python scripts/guard.py`) run instantly upon clone without waiting for 5+ minute retraining cycles.
  - Cryptographic immutability: the exact model weights used in verification candidate benchmarks are permanently preserved and matched to test predictions.
  - Size safety: at 26.09 MB maximum file size and 30.24 MB total bundle size, the payload is well below GitHub's 100 MB hard limit and 50 MB push warning threshold.
- **Cons**:
  - Incremental repository bloat if models are frequently retrained without git history squashing.

### Option 2: Git LFS
- **Pros**:
  - Keeps git commit history free of binary diffs during rapid iteration.
- **Cons**:
  - Requires `git-lfs` extension installed in all consumer, CI, and grading environments.
  - Adds external bandwidth quotas, token authentication complexities, and failure modes during automated shallow clones.
  - Overkill for a 30 MB static release bundle.

### Option 3: Ephemeral Rebuild via `make train`
- **Pros**:
  - Smallest initial clone size (< 5 MB).
- **Cons**:
  - High verification latency: retraining all 7 models, calibrating, computing conformal sets, and running bootstrap MCDA takes several minutes per run.
  - Risk of minor floating-point or dependency drift across disparate OS/architecture environments, potentially breaking exact test prediction SHA hashes.
  - Incompatible with the requirement to verify a frozen release candidate.

## Decision
We adopt **Option 1 (Direct Git Commit with Cryptographic Manifest)** for the `v2.0-verified-candidate` release:
1. **Direct Inclusion**: All artifacts under `artifacts/v2/` remain committed directly to git under explicit allowlist (`!artifacts/v2/` in `.gitignore`).
2. **Size Budget Policy**:
   - Single artifact maximum: 50.0 MB.
   - Total `artifacts/v2/` maximum: 60.0 MB.
   - Any model exceeding these thresholds must undergo pruning (e.g., limiting tree depth/count in Random Forest) before inclusion.
3. **Integrity Enforcement**: `artifacts/v2/MANIFEST.json` records SHA-256 hashes and byte lengths for all 54 files. Invariant Guard G8 verifies packet integrity against this manifest.
4. **Binary Attributes**: `.gitattributes` marks `*.joblib`, `*.pkl`, `*.db`, and `*.zip` as `binary` to prevent line-ending transformations.
5. **Future LFS Threshold**: If future versions (v3+) require deep learning weights or ensemble models exceeding 50 MB, Git LFS migration will be formally triggered under a separate ADR.

## Consequences
- Fresh clones of `v2.0-verified-candidate` are immediately operational and verifiable without additional build steps.
- CI and independent reviewers can verify champion performance and calibration metrics in seconds.
- The repository remains standard, portable, and free of external LFS infrastructure dependencies.
