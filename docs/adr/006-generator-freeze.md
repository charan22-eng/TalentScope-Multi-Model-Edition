# ADR 006: Data Generator Freeze for Multi-Model Edition

**Status:** Accepted
**Date:** 2026-10-08

## Context
In the Multi-Model Edition, we are evaluating 7 models on a fair playing field. If we observe model results and then tweak the data generator, we run a severe risk of creating "result-driven data design" (tuning the data to favor a particular model, such as making it easier for simple models or too convoluted, thereby favoring complex ones).

## Decision
We freeze the synthetic dataset generator (`ml/src/epk/data.py`) before any model is tuned or selected. We have validated the generator properties under three conditions (`linear`, `nonlinear` (default), and `noisy_overlap`), ensuring that different architectures are structurally favored under different data-generating assumptions.

**Final Parameters & Freeze Checksum:**
- Base rows: 12,000 (>= 10,000 post-cleaning)
- Noise: 0.45 for `linear`, 0.35 for `nonlinear`, 0.8 for `noisy_overlap`.
- Original SHA-256 Hash of `ml/src/epk/data.py`: `DE5F83AF47D92AD4DE5C9019CE07BEF5A7FAB3A9EB30549397B46C7D5B62134F`
- Amended SHA-256 Hash of `ml/src/epk/data.py`: `72248D00A23714FAC157E7E5438F4CA75FEA24D041425FE8CC0EE59FDC468305`

### Hash Definition & Normalization Specification
The frozen hash `72248D00A23714FAC157E7E5438F4CA75FEA24D041425FE8CC0EE59FDC468305` is defined exactly as the SHA-256 checksum over the LF-normalized byte content (all `\r\n` converted to `\n`, exactly 7,267 bytes) of `ml/src/epk/data.py`. This canonical representation corresponds to Git blob ID `db68c91211043b3883b522b71d037351aa7b7240` (identical at commit `5fba0e0` and repository `HEAD`).

### Amendment Note (2026-10-11)
- **Reason**: The realism layer in `ml/src/epk/data.py` previously injected 1.5% impossible values (exceeding the contract limit of <= 1%). It was amended to inject exactly 0.8% impossible values (96 rows) across `training_hours`, `weekly_hours`, and `attendance`. No changes were made to the data-generating process, latent factors, noise, or structure parameters.
- **Model Status**: No final model has been trained or evaluated against this amended dataset.

## Consequences
- No further tuning or adjustment of the synthetic generator is permitted, regardless of the subsequent model leaderboard outcomes.

