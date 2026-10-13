# ADR 012: Dual-Layer Dataset Checksum Strategy (Byte-Level LF and Row-Vector Hashing)

**Status:** Accepted  
**Date:** 2026-10-13  
**Deciders:** Core Engineering & ML Platform  

## Context
In TalentScope Multi-Model Edition, strict dataset integrity and reproducibility are enforced across 7 diverse machine learning models and multiple evaluation splits (train, cal-A, cal-B, locked test). Previously, dataset validation relied solely on a single byte-level SHA-256 checksum.

However, cross-platform environments (Windows Git checkouts converting `LF` to `CRLF` or vice-versa) exposed a subtle friction:
- While Git attributes (`.gitattributes`) enforce LF line endings, developer clones or local data generation scripts could produce CRLF line endings on Windows, altering raw byte-level hashes while preserving 100% identical numeric values and tabular rows.
- Conversely, relying exclusively on data frames without byte checksums sacrifices strict cryptographic provenance of raw data files.

## Decision
We establish a canonical, two-tiered checksum specification for all datasets in TalentScope:

1. **Primary Checksum (`sha256`)**:
   - Byte-level SHA-256 computed over the **LF-normalized raw bytes** (`\r\n` normalized to `\n`) of the CSV file.
   - Preserves strict byte-for-byte cryptographic integrity and matches standard POSIX tooling (`sha256sum`).
   
2. **Secondary Checksum (`row_hash_sha256`)**:
   - Semantic row-vector hash computed using `pd.util.hash_pandas_object(df, index=False)`.
   - The resulting array of 64-bit integer row hashes is serialized to continuous bytes (`.values.tobytes()`) and digested via SHA-256.
   - Provides line-ending-invariant, platform-independent verification that the table's schema, row order, column types, and cell values are identical regardless of file encoding or OS newline conventions.

### Alignment Across Manifests and System Locks
All system artifacts that reference dataset integrity use consistent definitions:
- **`data/manifest.json`**: Documents both primary `sha256` (LF-normalized) and secondary `row_hash_sha256` for every variant (`nonlinear`, `linear`, `noisy_overlap`).
- **`data/processed/split.json`**: Contains `dataset_sha256` (primary byte LF hash) and `row_hash_sha256`, verifying the disjoint partition indices against the canonical dataset.
- **`artifacts/v2/models/<key>/metadata.json`**: Records the frozen `split_hash` ensuring each model was tuned on the exact verified partition.
- **`reports/test_eval.lock`**: Locks the evaluation configuration to the primary `dataset_hash` and `split_hash`, preventing multiple test evaluations on differing data configurations (Guard G6).

## Consequences
- Cross-platform verification pipelines can detect whether a hash mismatch is a harmless line-ending difference or a true data corruption.
- Guard G1 and G5 maintain mathematically verifiable, non-ambiguous data locks.
