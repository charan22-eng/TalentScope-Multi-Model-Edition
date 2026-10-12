# Decisions Log

| Date | Decision ID | Question / Topic | Options Considered | Choice | Rationale | Cost of Reversing |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-10-12 | DEC-001 | Autonomous Build Protocol Execution | (A) Ask human at each step; (B) Full autonomous execution with DECIDE-AND-LOG | Option B | Follow explicit autonomous full-build prompt instructions. | Low |
| 2026-10-12 | DEC-002 | Default Model Specs and Estimators | (A) Support XGBoost/LightGBM; (B) HistGradientBoosting only | Option B | Adheres to prompt Section 6 defaults: HistGradientBoostingClassifier primary. | Low |
| 2026-10-12 | DEC-003 | Compute Profile for Build Phase | (A) Standard/Thorough; (B) Fast profile for build, locked final eval on standard | Option B | Section 4: PROFILE=fast during dev; make final PROFILE=standard on default variant. | Medium (re-running takes time) |
| 2026-10-12 | DEC-004 | Local LLM Engine Default Runtime | (A) Cloud APIs; (B) Local Ollama / OpenAI-compatible loopback | Option B | Section 6: Local-only, provider `ollama`, base URL `http://localhost:11434`, template fallback. | Low |
| 2026-10-12 | DEC-005 | Legacy Auth Reconciliation | (A) Keep default credentials; (B) Enforce environment JWT secret, remove hardcoded admin | Option B | High security hygiene requirement for Stage A2. | Low |
