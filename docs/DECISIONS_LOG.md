# Decisions Log

| Date | Decision ID | Question / Topic | Options Considered | Choice | Rationale | Cost of Reversing |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-12 | DEC-001 | Autonomous Build Protocol Execution | (A) Ask human at each step; (B) Full autonomous execution with DECIDE-AND-LOG | Option B | Follow explicit autonomous full-build prompt instructions. | Low |
| 2026-10-12 | DEC-002 | Default Model Specs and Estimators | (A) Support XGBoost/LightGBM; (B) HistGradientBoosting only | Option B | Adheres to prompt Section 6 defaults: HistGradientBoostingClassifier primary. | Low |
| 2026-10-12 | DEC-003 | Compute Profile for Build Phase | (A) Standard/Thorough; (B) Fast profile for build, locked final eval on standard | Option B | Section 4: PROFILE=fast during dev; make final PROFILE=standard on default variant. | Medium (re-running takes time) |
| 2026-10-12 | DEC-004 | Local LLM Engine Default Runtime | (A) Cloud APIs; (B) Local Ollama / OpenAI-compatible loopback | Option B | Section 6: Local-only, provider `ollama`, base URL `http://localhost:11434`, template fallback. | Low |
| 2026-10-12 | DEC-005 | Legacy Auth Reconciliation | (A) Keep default credentials; (B) Enforce environment JWT secret, remove hardcoded admin | Option B | High security hygiene requirement for Stage A2. | Low |
| 2026-10-12 | DEC-006 | Preprocessing Strategy | (A) Universal scaling; (B) Model-aware scaling (StandardScaler for lin/knn/svm; None for trees) | Option B | ADR-007: Prevents distortion in tree-based splits while ensuring convergence for distance/margin models. | Low |
| 2026-10-12 | DEC-007 | Calibration Policy | (A) Isotonic regression; (B) Platt scaling (sigmoid) on held-out Cal-A | Option B | ADR-008: Sigmoid prevents overfitting and preserves rank monotonicity on 1,190 cal-A samples. | Low |
| 2026-10-12 | DEC-008 | Champion Selection Rule | (A) Pure Macro-F1; (B) 5-profile MCDA with Dirichlet rank distribution & tie-breaking | Option B | ADR-009: Balanced multi-criteria optimization incorporating calibration, fairness, robustness, and latency. | Medium |
| 2026-10-12 | DEC-009 | Scope of Stage M | (A) Block release for wave 2 features; (B) Defer wave 2 features to focus on Stage N production hardening | Option B | Followed autonomous build defaults to deliver production-grade containerization, test coverage, and verifications. | Low |
| 2026-10-12 | DEC-010 | Database Strategy | (A) PostgreSQL only; (B) Dual dialect support (SQLite dev, PostgreSQL 16 docker-compose) | Option B | Enables zero-dependency local testing while providing production durability via SQLAlchemy models. | Low |
