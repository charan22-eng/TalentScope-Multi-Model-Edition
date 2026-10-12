# TalentScope Verification Progress

Tracking all verification checks in scope for `v2.0-rc` (Commit: `7cc244a079c69e8436ffe7eafebb7035a34f33d6`).

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
| **V0.1** | BLOCKING: Repository location and remote | H | todo | |
| **V0.2** | Clean-clone setup | H | todo | |
| **V0.3** | Python tests pass in clone | B | todo | |
| **V0.4** | Frontend lint, test, build in clone | B | todo | |
| **V0.5** | BLOCKING: Dependency integrity (R3F stack) | H | todo | |
| **V0.6** | Lock files committed | A | todo | |
| **V0.7** | CI green on GitHub | H | todo | |
| **V0.8** | Lint non-mutating in CI | B | todo | |
| **V0.9** | Ignore rules documented | A | todo | |
| **V0.10** | BLOCKING: No secrets in repo | B | todo | |
| **V0.11** | Docs present and consistent | B | todo | |
| **V0.12** | Evidence tooling works | A | todo | |
| **V0.13** | Red-flag baseline recorded | A | todo | |
| **V6.7** | BLOCKING: Upload & CSV sanitization (X10) | B | todo | |
| **V9.11** | BLOCKING: Privacy scan of telemetry/viz (X13) | B | todo | |
| **V10.2** | BLOCKING: Auth abuse / JWT verification (X9) | B | todo | |
| **V10.4** | BLOCKING: RBAC access matrix enforcement (X8) | B | todo | |
| **V10.8** | BLOCKING: Security headers and cookies (X24) | B | todo | |
| **V12.3** | BLOCKING: Audit log tamper resistance | B | todo | |
| **V13.5** | BLOCKING: Security audit (pip-audit / npm audit) (X24) | B | todo | |
| **V13.8** | BLOCKING: Regression test gates have teeth | B | todo | |
| **V14.4** | BLOCKING: Production deployment drill (X25) | B | todo | |
| **V15.2** | BLOCKING: Final numbers consistency across docs (X26) | B | todo | |

---

## 2. Multi-Model Checks (VM1 through VM12)

### VM1: Dataset v2 (12,000 Rows)
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM1.1** | BLOCKING: Row count >= 10,000 | B | todo | |
| **VM1.2** | Determinism across runs | H | todo | |
| **VM1.3** | Variant properties (independent check) | H | todo | |
| **VM1.4** | Sanity bands spread >= 0.08 | B | todo | |
| **VM1.5** | Class balance (30/45/25 +- 2%) | A | todo | |
| **VM1.6** | Score and band consistency | A | todo | |
| **VM1.7** | BLOCKING: Targets never in features | A | todo | |
| **VM1.8** | BLOCKING: Protected attributes isolated | B | todo | |
| **VM1.9** | Realism rates (missing 3-5%, dup <=1%, imp <=1%) | A | todo | |
| **VM1.10** | Generator frozen under hash | B | todo | |
| **VM1.11** | Documents updated (spec, dictionary, schema) | B | todo | |

### VM2: Preprocessing
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM2.1** | Model-aware factory | A | todo | |
| **VM2.2** | BLOCKING: Leakage test over all specs | A | todo | |
| **VM2.3** | BLOCKING: Mutation test fails when fit on full | H | todo | |
| **VM2.4** | Ordered labels [0, 1, 2] | A | todo | |
| **VM2.5** | Missing and unseen categories handled | A | todo | |
| **VM2.6** | Imputation parity across models | B | todo | |
| **VM2.7** | Nonlinearity evidence in EDA memo | B | todo | |
| **VM2.8** | Preprocessing ablation reproducible | H | todo | |

### VM3: Training and Evaluation
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM3.1** | BLOCKING: Same split for all models | A | todo | |
| **VM3.2** | BLOCKING: Test set used once (G6) | H | todo | |
| **VM3.3** | Equal tuning budget | A | todo | |
| **VM3.4** | Seven models present | A | todo | |
| **VM3.5** | ScoreToBand correctness | A | todo | |
| **VM3.6** | Search-space sanity (edge check) | A | todo | |
| **VM3.7** | Repeated splits stability std <= 0.02 | A | todo | |
| **VM3.8** | Training reproducibility (make train PROFILE=fast) | H | todo | |
| **VM3.9** | Independent replication of LogReg and RF | H | todo | |
| **VM3.10** | Cost metrics recorded | A | todo | |
| **VM3.11** | Too-good-to-be-true gate (< 0.97) | A | todo | |
| **VM3.12** | Regression track recorded for linreg | A | todo | |

### VM4: Comparison Science
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM4.1** | Bootstrap intervals (2,000 paired resamples) | A | todo | |
| **VM4.2** | Pairwise McNemar tests with Holm adjustment | A | todo | |
| **VM4.3** | Decision-strength rule unit tests | A | todo | |
| **VM4.4** | MCDA ranking reproduced independently | H | todo | |
| **VM4.5** | Dirichlet rank probabilities sum to 1 | A | todo | |
| **VM4.6** | Generator sensitivity across 3 variants | A | todo | |
| **VM4.7** | Calibration discipline (cal-A / cal-B disjoint) | A | todo | |
| **VM4.8** | Conformal coverage (87-95% at alpha 0.1) | B | todo | |
| **VM4.9** | Robustness and fairness per model | A | todo | |
| **VM4.10** | Evidence packet built by code | B | todo | |
| **VM4.11** | BLOCKING: No employee-level data in packet | A | todo | |
| **VM4.12** | Token budget <= 90 facts, <= 1200 tokens | A | todo | |

### VM5: Explainability
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM5.1** | Agnostic explainers on all models | A | todo | |
| **VM5.2** | Native explainers correct | A | todo | |
| **VM5.3** | KNN neighbours by hand | H | todo | |
| **VM5.4** | Honest labelling ("not how this model decided") | B | todo | |
| **VM5.5** | Counterfactual validity 100% | A | todo | |
| **VM5.6** | Spearman importance agreement reported | A | todo | |
| **VM5.7** | Surface grids 40x40 valid | A | todo | |
| **VM5.8** | Faithfulness top-feature removal >= 80% | A | todo | |
| **VM5.9** | Ranges within valid intervals | A | todo | |

### VM6: Local LLM Engine
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM6.1** | Health and discovery endpoint | A | todo | |
| **VM6.2** | BLOCKING: Local-only guard (SSRF) | A | todo | |
| **VM6.3** | BLOCKING: No employee-level data in prompts | H | todo | |
| **VM6.4** | Schema-constrained output | A | todo | |
| **VM6.5** | Validator test suite (rejects invalid, accepts valid) | A | todo | |
| **VM6.6** | Golden evaluation with real model | B | todo | |
| **VM6.7** | Injection resistance against poisoned packet | H | todo | |
| **VM6.8** | Determinism at temperature 0 | A | todo | |
| **VM6.9** | Fallback template on failure | A | todo | |
| **VM6.10** | Decision strength honoured (never "clear" under marginal) | A | todo | |
| **VM6.11** | Latency and hardware recorded | A | todo | |
| **VM6.12** | Verdict persistence and caching | A | todo | |
| **VM6.13** | Human read-through of 10 outputs | H | todo | |
| **VM6.14** | Second-opinion disagreement flagged | A | todo | |

### VM7: Artifacts v2
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM7.1** | Layout and SHA-256 manifest | A | todo | |
| **VM7.2** | BLOCKING: Tamper detection refuses modified file | H | todo | |
| **VM7.3** | Per-model metadata complete | A | todo | |
| **VM7.4** | Rebuild reproducibility | B | todo | |
| **VM7.5** | Model cards match machine files | B | todo | |
| **VM7.6** | Champion record valid | A | todo | |
| **VM7.7** | Golden-input regression tests pass | A | todo | |
| **VM7.8** | Cold start under 10 seconds | A | todo | |

### VM8: API v2
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM8.1** | v1 compatibility preserved | A | todo | |
| **VM8.2** | Models endpoint returns 7 models | A | todo | |
| **VM8.3** | Predict per model matches pipeline | A | todo | |
| **VM8.4** | Predict-all latency p95 < 800ms | H | todo | |
| **VM8.5** | Compare endpoints match files without recompute | A | todo | |
| **VM8.6** | MCDA endpoint validates weights | A | todo | |
| **VM8.7** | LLM endpoint roles and rate limits | A | todo | |
| **VM8.8** | OpenAPI spec synchronized | H | todo | |
| **VM8.9** | BLOCKING: Whitelist and traversal refused | A | todo | |
| **VM8.10** | 503 problem details on LLM unavailable | A | todo | |

### VM9: Core Frontend Pages
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM9.1** | Predict-all parity between UI and API | A | todo | |
| **VM9.2** | Agreement logic and split-decision flag | A | todo | |
| **VM9.3** | Batch multi-model 5,000 rows | B | todo | |
| **VM9.4** | Model Lab displays "Experimental, not deployed" | B | todo | |
| **VM9.5** | UI equals API across cases | A | todo | |
| **VM9.6** | Accessibility (axe and keyboard, 0 serious) | A | todo | |
| **VM9.7** | Console 0 errors on navigation | B | todo | |

### VM10: Model Arena
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM10.1** | Leaderboard UI equals leaderboard.json | A | todo | |
| **VM10.2** | Accessible palette (Okabe-Ito, table views) | A | todo | |
| **VM10.3** | Head-to-head equals pairwise.json | A | todo | |
| **VM10.4** | Priorities dynamic MCDA matches server | B | todo | |
| **VM10.5** | Rank probability chart matches server | A | todo | |
| **VM10.6** | Sensitivity bump chart shows 3 variants | A | todo | |
| **VM10.7** | LLM panel features operational | B | todo | |
| **VM10.8** | LLM text numbers equal facts | H | todo | |
| **VM10.9** | Decision strength messaging correct | A | todo | |
| **VM10.10** | Arena LCP under 2.5s | A | todo | |
| **VM10.11** | Lighthouse accessibility >= 90 | A | todo | |
| **VM10.12** | Screenshots saved with SHA and date | A | todo | |

### VM11: 3D Experiences
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM11.1** | Landscape cells equal predict_proba (1e-9) | A | todo | |
| **VM11.2** | Difference surface equals P_A - P_B | A | todo | |
| **VM11.3** | 2D heatmap fallback operational | H | todo | |
| **VM11.4** | Performance budget >= 50 fps, < 100 draw calls | H | todo | |
| **VM11.5** | No memory growth on model switching | A | todo | |
| **VM11.6** | Privacy: opaque IDs only in 3D payloads | A | todo | |

### VM12: Security, MLOps, Deployment
| Check ID | Description | Type | Status | Evidence Path |
|---|---|---|---|---|
| **VM12.1** | RBAC matrix enforced across all routes | H | todo | |
| **VM12.2** | Migrations upgrade and downgrade succeed | A | todo | |
| **VM12.3** | Retrain-all keeps holdout hash unchanged | H | todo | |
| **VM12.4** | Champion promotion rule enforced | A | todo | |
| **VM12.5** | Drift monitoring detects injected drift | A | todo | |
| **VM12.6** | Shadow mode evaluates runner-up model | A | todo | |
| **VM12.7** | Works fully with LLM offline | H | todo | |
| **VM12.8** | Documentation complete with caveats | B | todo | |

---

## 3. Adversarial & Independent Tests (X1 through X26)
- X1 Leakage mutation (VM2.3)
- X2 Generator freeze (VM1.10)
- X3 Test-set-once lock (VM3.2)
- X4 Artifact tamper detection (VM7.2)
- X5 Validator attack set (VM6.5)
- X6 Prompt injection resistance (VM6.7)
- X7 LLM unavailable fallback (VM6.9)
- X8 Access control matrix (V10.4, VM12.1)
- X9 Auth abuse & JWT verification (V10.2)
- X10 Upload & CSV sanitization (V6.7)
- X11 Model-key traversal attack (VM8.9)
- X12 LLM SSRF URL abuse (VM6.2)
- X13 Privacy scan (VM6.3, VM9, V9.11)
- X14 Reproducibility of training & manifests (VM3.8, VM7.4)
- X15 Label-order trap (VM2.4)
- X16 Independent metric replication (VM3, VM4.1, VM4.2)
- X17 Independent MCDA replication (VM4.4, VM4.5)
- X18 Independent conformal coverage recomputation (VM4.8)
- X19 Independent retraining of LogReg & RF (VM3.9)
- X20 KNN neighbours by hand & counterfactuals (VM5.3, VM5.5)
- X21 Surface cell verification (VM11.1, VM11.2)
- X22 Performance benchmarks & load test (VM8.4, V13.3)
- X23 Frontend automation (axe/Lighthouse)
- X24 Security tooling (pip-audit, npm audit, bandit, git secret scan) (V13.4-V13.7)
- X25 Containerization & deployment drill (V14.x)
- X26 Numbers consistency audit (V15.3, VM7.5)
