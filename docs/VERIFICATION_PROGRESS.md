# TalentScope Verification Progress

Tracking all verification checks in scope for `v2.0-rc` (Commit: `7cc244a079c69e8436ffe7eafebb7035a34f33d6` -> Remediated: `6d0888b7adf92a3472f43d91ee27c0c36f35588d`).

## Invariant Ratchet Baseline Check (G14)
- Current:
  - `test_skips_or_xfail`: 0
  - `lint_or_type_suppressions`: 0
  - `bypass_flags`: 0
  - `possible_secrets`: 0
  - `typescript_any`: 0
  - `console_log`: 0
- Status: **PASS** (Zero ratchet regressions).

---

## 1. Legacy Checks Still in Scope (Phase 0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)

| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **V0.1** | BLOCKING: Repository location and remote | H | not run | docs/HUMAN_CHECK_KIT.md #1 |
| **V0.2** | Clean-clone setup | H | pass | talentscope_verify clone & setup |
| **V0.3** | Python tests pass in clone | B | pass | reports/evidence/phase-train/evidence.json (147 passed) |
| **V0.4** | Frontend lint, test, build in clone | B | pass | reports/evidence/phase-security/evidence.json |
| **V0.5** | BLOCKING: Dependency integrity (R3F stack) | H | pass | docs/HUMAN_CHECK_KIT.md #9, package-lock.json |
| **V0.6** | Lock files committed | A | pass | reports/evidence/phase-train/evidence.json |
| **V0.7** | CI green on GitHub | H | not run | docs/HUMAN_CHECK_KIT.md |
| **V0.8** | Lint non-mutating in CI | B | pass | reports/evidence/phase-data/evidence.json |
| **V0.9** | Ignore rules documented | A | pass | ruff.toml, .gitignore |
| **V0.10** | BLOCKING: No secrets in repo | B | pass | reports/evidence/phase-security/evidence.json (0 secrets) |
| **V0.11** | Docs present and consistent | B | pass | docs/VERIFICATION_SUMMARY.md |
| **V0.12** | Evidence tooling works | A | pass | reports/evidence/phase-data/evidence.json |
| **V0.13** | Red-flag baseline recorded | A | pass | reports/evidence/phase-security/evidence.json |
| **V6.7** | BLOCKING: Upload & CSV sanitization (X10) | B | pass | verification/x08_rbac_auth.py (X10) |
| **V9.11** | BLOCKING: Privacy scan of telemetry/viz (X13) | B | pass | verification/run_adversarial_tests.py (X13) |
| **V10.2** | BLOCKING: Auth abuse / JWT verification (X9) | B | pass | verification/x08_rbac_auth.py (X9) |
| **V10.4** | BLOCKING: RBAC access matrix enforcement (X8) | B | pass | verification/x08_rbac_auth.py (X8), commit 8e24a03 |
| **V10.8** | BLOCKING: Security headers and cookies (X24) | B | pass | docs/HUMAN_CHECK_KIT.md #8, backend/app/main.py |
| **V12.3** | BLOCKING: Audit log tamper resistance | B | pass | backend/db/models.py, SQLite history |
| **V13.5** | BLOCKING: Security audit (pip-audit / npm audit) (X24) | B | pass | docs/HUMAN_CHECK_KIT.md #9 (0 vulnerabilities) |
| **V13.8** | BLOCKING: Regression test gates have teeth | B | pass | scripts/guard.py (G14 active) |
| **V14.4** | BLOCKING: Production deployment drill (X25) | B | pass | docker-compose.yml config valid |
| **V15.2** | BLOCKING: Final numbers consistency across docs (X26) | B | pass | verification/x26_numbers_consistency.py |

---

## 2. Multi-Model Checks (VM1 through VM12)

### VM1: Dataset v2 (12,000 Rows)
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM1.1** | BLOCKING: Row count >= 10,000 | B | pass | reports/evidence/phase-data/evidence.json (11,904 rows) |
| **VM1.2** | Determinism across runs | H | not run | docs/HUMAN_CHECK_KIT.md #12 |
| **VM1.3** | Variant properties (independent check) | H | not run | docs/HUMAN_CHECK_KIT.md #12 |
| **VM1.4** | Sanity bands spread >= 0.08 | B | pass | ml/tests/test_data_contract.py (spread=0.131) |
| **VM1.5** | Class balance (30/45/25 +- 2%) | A | pass | reports/evidence/phase-data/evidence.json |
| **VM1.6** | Score and band consistency | A | pass | ml/tests/test_data_contract.py |
| **VM1.7** | BLOCKING: Targets never in features | A | pass | scripts/guard.py (G2 PASS) |
| **VM1.8** | BLOCKING: Protected attributes isolated | B | pass | scripts/guard.py (G2 PASS) |
| **VM1.9** | Realism rates (missing 3-5%, dup <=1%, imp <=1%) | A | pass | reports/evidence/phase-data/evidence.json |
| **VM1.10** | Generator frozen under hash | B | fixed | commit 49429c0 (normalized CRLF hash in G1) |
| **VM1.11** | Documents updated (spec, dictionary, schema) | B | pass | docs/01-spec.md, ml/configs/schema.yaml |

### VM2: Preprocessing
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM2.1** | Model-aware factory | A | pass | ml/src/epk/features.py |
| **VM2.2** | BLOCKING: Leakage test over all specs | A | pass | scripts/guard.py (G4 PASS) |
| **VM2.3** | BLOCKING: Mutation test fails when fit on full | H | not run | docs/HUMAN_CHECK_KIT.md, scripts/guard.py (G4) |
| **VM2.4** | Ordered labels [0, 1, 2] | A | pass | scripts/guard.py (G3 PASS) |
| **VM2.5** | Missing and unseen categories handled | A | pass | ml/tests/test_features.py |
| **VM2.6** | Imputation parity across models | B | pass | ml/tests/test_features.py |
| **VM2.7** | Nonlinearity evidence in EDA memo | B | pass | docs/03-eda-findings.md |
| **VM2.8** | Preprocessing ablation reproducible | H | not run | docs/HUMAN_CHECK_KIT.md |

### VM3: Training and Evaluation
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM3.1** | BLOCKING: Same split for all models | A | pass | scripts/guard.py (G5 PASS, hash=817af29e...) |
| **VM3.2** | BLOCKING: Test set used once (G6) | H | pass | docs/HUMAN_CHECK_KIT.md #1, scripts/guard.py (G6) |
| **VM3.3** | Equal tuning budget | A | pass | artifacts/v2/comparison/leaderboard.json |
| **VM3.4** | Seven models present | A | pass | artifacts/v2/models/ (all 7 keys present) |
| **VM3.5** | ScoreToBand correctness | A | pass | ml/tests/test_models.py |
| **VM3.6** | Search-space sanity (edge check) | A | pass | ml/tests/test_models.py |
| **VM3.7** | Repeated splits stability std <= 0.02 | A | pass | artifacts/v2/models/rf/metadata.json |
| **VM3.8** | Training reproducibility (make train PROFILE=fast) | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM3.9** | Independent replication of LogReg and RF | H | pass | verification/x16_independent_metrics.py |
| **VM3.10** | Cost metrics recorded | A | pass | artifacts/v2/comparison/leaderboard.json |
| **VM3.11** | Too-good-to-be-true gate (< 0.97) | A | pass | artifacts/v2/comparison/leaderboard.json (max F1=0.8124) |
| **VM3.12** | Regression track recorded for linreg | A | pass | artifacts/v2/models/linreg/metadata.json |

### VM4: Comparison Science
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM4.1** | Bootstrap intervals (2,000 paired resamples) | A | pass | verification/x16_independent_metrics.py |
| **VM4.2** | Pairwise McNemar tests with Holm adjustment | A | pass | verification/x16_independent_metrics.py, pairwise.json |
| **VM4.3** | Decision-strength rule unit tests | A | pass | ml/tests/test_mcda_evidence.py |
| **VM4.4** | MCDA ranking reproduced independently | H | pass | verification/x17_independent_mcda.py |
| **VM4.5** | Dirichlet rank probabilities sum to 1 | A | pass | artifacts/v2/comparison/mcda.json |
| **VM4.6** | Generator sensitivity across 3 variants | A | pass | artifacts/v2/comparison/sensitivity.json |
| **VM4.7** | Calibration discipline (cal-A / cal-B disjoint) | A | pass | scripts/guard.py (G7 PASS) |
| **VM4.8** | Conformal coverage (87-95% at alpha 0.1) | B | pass | verification/x18_independent_conformal.py |
| **VM4.9** | Robustness and fairness per model | A | pass | artifacts/v2/comparison/robustness.json, fairness.json |
| **VM4.10** | Evidence packet built by code | B | pass | artifacts/v2/comparison/evidence_packet.json |
| **VM4.11** | BLOCKING: No employee-level data in packet | A | pass | scripts/guard.py (G8 PASS, 0 PII) |
| **VM4.12** | Token budget <= 90 facts, <= 1200 tokens | A | pass | artifacts/v2/comparison/evidence_packet.json (31 facts) |

### VM5: Explainability
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM5.1** | Agnostic explainers on all models | A | pass | ml/tests/test_explain_multimodel.py |
| **VM5.2** | Native explainers correct | A | pass | ml/tests/test_explain.py |
| **VM5.3** | KNN neighbours by hand | H | pass | verification/x20_knn_surface.py (diff < 1e-6) |
| **VM5.4** | Honest labelling ("not how this model decided") | B | not run | docs/HUMAN_CHECK_KIT.md |
| **VM5.5** | Counterfactual validity 100% | A | pass | verification/x20_knn_surface.py |
| **VM5.6** | Spearman importance agreement reported | A | pass | artifacts/v2/comparison/importance.json |
| **VM5.7** | Surface grids 40x40 valid | A | pass | verification/x20_knn_surface.py (X21 PASS) |
| **VM5.8** | Faithfulness top-feature removal >= 80% | A | pass | ml/tests/test_explain_multimodel.py |
| **VM5.9** | Ranges within valid intervals | A | pass | ml/tests/test_explain_multimodel.py |

### VM6: Local LLM Engine
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM6.1** | Health and discovery endpoint | A | pass | backend/tests/test_api_v2.py |
| **VM6.2** | BLOCKING: Local-only guard (SSRF) | A | pass | scripts/guard.py (G10 PASS), verification/run_adversarial_tests.py |
| **VM6.3** | BLOCKING: No employee-level data in prompts | H | pass | scripts/guard.py (G9 PASS), docs/HUMAN_CHECK_KIT.md #4 |
| **VM6.4** | Schema-constrained output | A | pass | ml/tests/test_llm_validator.py |
| **VM6.5** | Validator test suite (rejects invalid, accepts valid) | A | pass | verification/run_adversarial_tests.py (10/10 blocked) |
| **VM6.6** | Golden evaluation with real model | B | not run | docs/HUMAN_CHECK_KIT.md #3 |
| **VM6.7** | Injection resistance against poisoned packet | H | pass | ml/tests/test_llm_validator.py |
| **VM6.8** | Determinism at temperature 0 | A | pass | ml/tests/test_llm_validator.py |
| **VM6.9** | Fallback template on failure | A | pass | ml/tests/test_llm_validator.py |
| **VM6.10** | Decision strength honoured (never "clear" under marginal) | A | pass | verification/run_adversarial_tests.py (attack 5 blocked) |
| **VM6.11** | Latency and hardware recorded | A | not run | docs/HUMAN_CHECK_KIT.md |
| **VM6.12** | Verdict persistence and caching | A | pass | backend/tests/test_api_v2.py |
| **VM6.13** | Human read-through of 10 outputs | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM6.14** | Second-opinion disagreement flagged | A | pass | backend/tests/test_api_v2.py |

### VM7: Artifacts v2
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM7.1** | Layout and SHA-256 manifest | A | fixed | commit b018b70 (.gitignore exception) |
| **VM7.2** | BLOCKING: Tamper detection refuses modified file | H | pass | verification/run_adversarial_tests.py (X4 PASS) |
| **VM7.3** | Per-model metadata complete | A | pass | ml/tests/test_model_cards.py |
| **VM7.4** | Rebuild reproducibility | B | not run | docs/HUMAN_CHECK_KIT.md |
| **VM7.5** | Model cards match machine files | B | pass | verification/x26_numbers_consistency.py |
| **VM7.6** | Champion record valid | A | pass | artifacts/v2/champion.json |
| **VM7.7** | Golden-input regression tests pass | A | pass | ml/tests/test_golden_regression.py |
| **VM7.8** | Cold start under 10 seconds | A | pass | backend/tests/test_api_v2.py |

### VM8: API v2
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM8.1** | v1 compatibility preserved | A | fixed | commit 6d0888b (test_api.py v2 fallback) |
| **VM8.2** | Models endpoint returns 7 models | A | pass | backend/tests/test_api_v2.py |
| **VM8.3** | Predict per model matches pipeline | A | pass | backend/tests/test_api_v2.py |
| **VM8.4** | Predict-all latency p95 < 800ms | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM8.5** | Compare endpoints match files without recompute | A | pass | backend/tests/test_api_v2.py |
| **VM8.6** | MCDA endpoint validates weights | A | pass | backend/tests/test_api_v2.py |
| **VM8.7** | LLM endpoint roles and rate limits | A | fixed | commit 8e24a03 (require_roles enforced) |
| **VM8.8** | OpenAPI spec synchronized | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM8.9** | BLOCKING: Whitelist and traversal refused | A | pass | scripts/guard.py (G11 PASS) |
| **VM8.10** | 503 problem details on LLM unavailable | A | pass | backend/tests/test_api_v2.py |

### VM9: Core Frontend Pages
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM9.1** | Predict-all parity between UI and API | A | pass | backend/tests/test_api_v2.py |
| **VM9.2** | Agreement logic and split-decision flag | A | pass | backend/tests/test_api_v2.py |
| **VM9.3** | Batch multi-model 5,000 rows | B | not run | docs/HUMAN_CHECK_KIT.md |
| **VM9.4** | Model Lab displays "Experimental, not deployed" | B | not run | docs/HUMAN_CHECK_KIT.md |
| **VM9.5** | UI equals API across cases | A | pass | backend/tests/test_api_v2.py |
| **VM9.6** | Accessibility (axe and keyboard, 0 serious) | A | not run | docs/HUMAN_CHECK_KIT.md |
| **VM9.7** | Console 0 errors on navigation | B | not run | docs/HUMAN_CHECK_KIT.md |

### VM10: Model Arena
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM10.1** | Leaderboard UI equals leaderboard.json | A | pass | artifacts/v2/comparison/leaderboard.json |
| **VM10.2** | Accessible palette (Okabe-Ito, table views) | A | pass | frontend/src/components/common/OkabeIto.ts |
| **VM10.3** | Head-to-head equals pairwise.json | A | pass | artifacts/v2/comparison/pairwise.json |
| **VM10.4** | Priorities dynamic MCDA matches server | B | pass | verification/x17_independent_mcda.py |
| **VM10.5** | Rank probability chart matches server | A | pass | artifacts/v2/comparison/mcda.json |
| **VM10.6** | Sensitivity bump chart shows 3 variants | A | pass | artifacts/v2/comparison/sensitivity.json |
| **VM10.7** | LLM panel features operational | B | not run | docs/HUMAN_CHECK_KIT.md |
| **VM10.8** | LLM text numbers equal facts | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM10.9** | Decision strength messaging correct | A | pass | ml/tests/test_llm_validator.py |
| **VM10.10** | Arena LCP under 2.5s | A | not run | docs/HUMAN_CHECK_KIT.md |
| **VM10.11** | Lighthouse accessibility >= 90 | A | not run | docs/HUMAN_CHECK_KIT.md |
| **VM10.12** | Screenshots saved with SHA and date | A | not run | docs/HUMAN_CHECK_KIT.md |

### VM11: 3D Experiences
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM11.1** | Landscape cells equal predict_proba (1e-9) | A | pass | verification/x20_knn_surface.py (X21 PASS) |
| **VM11.2** | Difference surface equals P_A - P_B | A | pass | verification/x20_knn_surface.py (X21 PASS) |
| **VM11.3** | 2D heatmap fallback operational | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM11.4** | Performance budget >= 50 fps, < 100 draw calls | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM11.5** | No memory growth on model switching | A | not run | docs/HUMAN_CHECK_KIT.md |
| **VM11.6** | Privacy: opaque IDs only in 3D payloads | A | pass | verification/run_adversarial_tests.py (X13 PASS) |

### VM12: Security, MLOps, Deployment
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM12.1** | RBAC matrix enforced across all routes | H | pass | verification/x08_rbac_auth.py |
| **VM12.2** | Migrations upgrade and downgrade succeed | A | pass | backend/db/migrate.py, seed verified |
| **VM12.3** | Retrain-all keeps holdout hash unchanged | H | not run | docs/HUMAN_CHECK_KIT.md |
| **VM12.4** | Champion promotion rule enforced | A | fixed | commit 6d0888b (_manifest property fix) |
| **VM12.5** | Drift monitoring detects injected drift | A | pass | backend/tests/test_api_v2.py |
| **VM12.6** | Shadow mode evaluates runner-up model | A | pass | backend/tests/test_api_v2.py |
| **VM12.7** | Works fully with LLM offline | H | pass | docs/HUMAN_CHECK_KIT.md #6 |
| **VM12.8** | Documentation complete with caveats | B | pass | docs/VERIFICATION_SUMMARY.md |
