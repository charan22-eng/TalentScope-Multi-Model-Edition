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
- SHA-256 Hash of `ml/src/epk/data.py`: `DE5F83AF47D92AD4DE5C9019CE07BEF5A7FAB3A9EB30549397B46C7D5B62134F`

## Consequences
- No further tuning or adjustment of the synthetic generator is permitted, regardless of the subsequent model leaderboard outcomes.
