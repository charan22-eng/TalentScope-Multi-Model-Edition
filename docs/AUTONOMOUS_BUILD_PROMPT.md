<USER_REQUEST>
/plan /build-app /zero-to-deploy 

HOW TO USE THIS FILE (not part of the prompt)
1. Pre-flight (10 minutes, strongly recommended before launching a long autonomous run): (a) copy the ORIGINAL downloaded
   TalentScope_MultiModel_Edition_Prompt_Pack.md over docs/MULTIMODEL_PACK.md and commit it; (b) run the human checks VM1.2
   and VM1.3 (determinism and the independent 7-model variant check) so a data problem is found BEFORE eleven stages are
   built on top of it; (c) make sure `git status` is clean; (d) optional: start your local LLM runtime (the build works
   without it, and the real-model evaluation is deferred to verification).
2. Paste everything from the line "PASTE FROM HERE" to the end into the coding agent as ONE message.
3. The run is long. If the agent loses context or stops, paste the SAME prompt again: it resumes from docs/BUILD_PROGRESS.md.
4. When the agent reports "BUILD COMPLETE", open a NEW chat/session (fresh context) and paste file 02 (verification prompt).
   Do not let the builder verify its own work.

========================== PASTE FROM HERE ==========================

# TALENTSCOPE MULTI-MODEL: AUTONOMOUS FULL-BUILD PROMPT

## 1. MISSION

You are the same two senior engineers as in the Master Build Prompt and the Multi-Model Addendum (a senior data mining
engineer and a senior full-stack/AI engineer). Complete the ENTIRE remaining TalentScope Multi-Model project in this run,
Stage A to Stage N below, WITHOUT asking me for approval, confirmation or clarification between stages or tasks.
Verification evidence (VM checks, evidence JSON, log filling) is deferred to a SEPARATE verification run by a different
session. Your job now: build everything correctly, keep the guard suite green, commit cleanly, and leave a truthful
build report. Do not claim any verification check passed.

Facts to rely on (re-check them with git before using them):
- MM-S1 is done. Dataset v2 lives in data/{linear,nonlinear,noisy_overlap}/{dataset.csv,protected.csv} with data/manifest.json.
- The generator is frozen by docs/adr/006-generator-freeze.md. Its latest recorded SHA-256 is
  72248D00A23714FAC157E7E5438F4CA75FEA24D041425FE8CC0EE59FDC468305 (amended once, before any model was trained).
- Last MM-S1 evidence commit: 9ccae4c81f87a7861bdcef304c4c6127dfb488d6. Human checks VM1.2 and VM1.3 may still be pending.
- The repo contains frontend/backend code from earlier sessions (3D SceneFrame kit, auth integration, protected routes,
  drift monitoring, Playwright specs) that was committed in bulk WITHOUT review. Treat all of it as UNTRUSTED LEGACY
  until Stage A has classified it.
- Authoritative specs: docs/MULTIMODEL_PACK.md (Parts 2 to 6 and the tested reference code in Part 10), the Master Build
  Prompt, the Multi-Model Addendum, docs/PHASES_AND_VERIFICATION.md. Read the relevant parts at the start of each stage.

## 2. AUTONOMY RULES (so you never need to ask me anything)

1. DECIDE-AND-LOG. Any question you would normally ask me: choose the safest, most conservative option consistent with the
   specs, write it to docs/DECISIONS_LOG.md (date, question, options, choice, reason, cost of reversing), and continue.
   Use section 6 (decision defaults) first.
2. HARD STOPS (the ONLY reasons to stop and wait for me): (a) a credential, secret or paid service is required;
   (b) an action would delete or overwrite data outside the repository, or require reading files outside the repository
   (never read your own transcript or system logs); (c) a guard invariant cannot be restored after 3 honest attempts
   (for example leakage cannot be eliminated); (d) the working tree contains uncommitted changes you did not make;
   (e) any change to ml/src/epk/data.py would be needed after Stage C has started. On a hard stop: write docs/BLOCKERS.md
   (what, why, what you tried, what you need), commit, and stop with a short message.
3. NOT hard stops: the local LLM runtime being absent (use the fake LLM for tests and the template fallback; the real-model
   golden evaluation is deferred and recorded as "pending real model"); a library API differing from the pack (read the
   current docs, adapt, log it); a test you wrote failing (fix the code, never weaken the test).
4. NEVER: weaken or delete a test, threshold or check to make something pass; change the frozen generator; fabricate or
   hand-type any metric; commit secrets; use --legacy-peer-deps, --no-verify, --force or --break-system-packages;
   add a dependency without an ADR; add test skips, lint or type suppressions, or `any` beyond the ratchet baseline (G14);
   bundle unrelated work into one commit; read files outside the repository; claim verification.
5. RESUME PROTOCOL. After every task update docs/BUILD_PROGRESS.md (checklist IDs from section 5, status, commit SHA) and
   docs/STATE.md. If you lose context or I paste this prompt again, read docs/BUILD_PROGRESS.md and docs/STATE.md, run
   `make guard`, and continue at the first unchecked item. Never redo a completed stage unless guard fails.
6. GIT DISCIPLINE. One logical task per commit with a conventional message (feat:, fix:, test:, docs:, chore:, refactor:).
   Commits stay small (roughly under 400 changed lines unless generated). Tag each finished stage `stage-<letter>-built`.
   Keep the working tree clean at every stage boundary. Push if a remote is configured.
7. COMMUNICATION. Do not ask questions. Print one short progress line at each stage boundary. At the very end print the
   final report described in section 7.
8. PRIORITY ORDER when time is short: guards and correctness > Stages A to L > Stage N (delivery) > Stage M (optional).
   Never skip a guard to save time.

## 3. THE GUARD SUITE (`make guard`, must stay green after EVERY task)

Create `make guard` in Stage A and extend it as components appear (the stage that creates a component also adds its
guards; list planned guards in docs/BUILD_PROGRESS.md; do not use pytest skips as placeholders). Target runtime under
5 minutes (use small fixtures). Invariants:

- G1 Generator frozen: SHA-256 of ml/src/epk/data.py equals the latest hash in ADR-006. After Stage C starts (any model row
  in reports/experiments.csv) the generator is permanently frozen and the guard fails on any difference.
- G2 Targets (performance, performance_score), employee_id and protected columns never appear in any feature list.
- G3 Ordered labels: classes_ == [0, 1, 2] for every fitted registry model.
- G4 Leakage test parametrised over every registry spec (train-only fitting), plus a documented mutation script.
- G5 Split frozen: data/processed/split.json hash equals the recorded hash; train, cal-A, cal-B and test are disjoint.
- G6 Test-set-once: test evaluation happens ONLY through `make final`. It writes reports/test_eval.lock (variant, config hash,
  dataset hash, split hash, UTC time) and refuses to run again for the same key. A different configuration needs
  `--new-config "<reason>"`, which appends a row to reports/test_eval_log.csv. A static test proves no code outside
  ml/src/epk/final_eval.py reads the test indices.
- G7 cal-A and cal-B are never used in tuning code (static and dynamic test).
- G8 The evidence packet contains no employee-level data (forbidden-key scan) and every fact is generated from files.
- G9 LLM validator suite: at least 12 failing and 4 passing cases; no prompt contains forbidden keys.
- G10 Local-only LLM guard (public host refused, private allowed, remote only with explicit flag).
- G11 Model-key whitelist (no path traversal) and /api/v1 backward-compatibility tests.
- G12 RBAC matrix tests (role by route, generated from the OpenAPI file) including LLM and Arena routes.
- G13 No secrets: `python scripts/redflags.py` reports possible_secrets 0 and bypass_flags 0.
- G14 Ratchet: counts of test skips, lint/type suppressions, `any`, console.log may only go DOWN from the baseline recorded in
  docs/BUILD_PROGRESS.md (an unconditional skip must be an explicit skipif with a reason and an obligation ID).

## 4. COMPUTE AND DATA DEFAULTS

- Development: PROFILE=fast, cross-validation or validation data only. No test-set use outside `make final`.
- Final artifacts: run `make final PROFILE=standard` for the default (nonlinear) variant once, at the end of Stage C. If that
  would exceed about 3 hours on this machine, use fast, log the decision and the measured time.
- Sensitivity variants: Stage D runs the pipeline once per variant through `make final-variants` (a lock per variant).
- Persist per-model test predictions as artifacts/v2/models/<key>/test_predictions.csv (row index, y_true, y_pred, class
  probabilities; git-ignored) so a separate verifier can recompute metrics independently.
- If a later stage needs a retrain, use `--new-config "<reason>"` and rebuild downstream files. Prefer fixing downstream code.

## 5. STAGES (checklist IDs are used in docs/BUILD_PROGRESS.md)

### Stage A: Audit, hygiene, guard suite  (tag stage-a-built)
- A1 Inventory: write docs/INVENTORY.md classifying every backend route, frontend page/component, DB model, script, test
  and dependency as KEEP, REFACTOR, REMOVE or SECURITY-REVIEW. Pay special attention to auth integration, protected routes,
  drift monitoring, SceneFrame/3D kit and Playwright specs.
- A2 Security review of legacy auth: password hashing, JWT secret from environment (no default), token expiry, cookie flags,
  route guards, no default admin credentials. Fix or replace what is unsafe.
- A3 Hygiene: remove `any` (target 0 outside generated types), console.log in tests, dead code. Record the G14 baseline.
- A4 Create `make guard` with G1, G2, G13, G14 now; add the others as their components appear.
- A5 Create docs/BUILD_PROGRESS.md (this checklist), docs/DECISIONS_LOG.md; write ADR-010 reconciling legacy code with the
  multi-model architecture. Record obligation O1: re-enable the skipped v1 golden tests in Stage H.

### Stage B: Preprocessing for seven models (MM-S2, pack 7.2)  (tag stage-b-built)
- B1 EDA notebook on the default variant including nonlinearity evidence (saturation, U-shape, threshold, interaction);
  docs/03-eda-findings.md with every decision linked to evidence.
- B2 ModelSpec dataclass and seven spec stubs (key, label, family, task, needs_scaling, explain_tier).
- B3 `build_preprocessor(spec)`: scaler only if needed, median imputation, ordinal job_level, one-hot department,
  Winsorizer fitted on train only; documented exceptions only.
- B4 Ordered integer label encoding in exactly one place.
- B5 Tests: shapes, no NaN or inf, idempotence, unseen categories, division safety; parametrised leakage test (G4);
  mutation script under ml/scripts/ that fits on all data and must make the leakage test fail.
- B6 Ablation on two representative models (one scaled, one tree), logged to reports/experiments.csv (CV only); ADR-007.

### Stage C: Registry, training, final evaluation (MM-S3, pack 7.3)  (tag stage-c-built)
- C1 ml/src/epk/models/registry.py with ModelSpec and ScoreToBand (pack section 10.2: read, test, adapt); one spec file per
  model: linreg, logreg, knn, svm, dt, rf, boost (histogram gradient boosting only).
- C2 Frozen split 60/20/20 (seed 42), calibration split halved into cal-A and cal-B, data/processed/split.json with hash (G5, G7).
- C3 `train_all.py --profile {fast,standard,thorough}`: random search with identical iterations, identical inner stratified
  5-fold CV, scoring macro-F1, identical seeds; linreg fitted directly; SVM tuned with probability=False. Runs logged to
  reports/experiments.csv (model, params, CV mean/std, seed, dataset checksum, split hash, profile).
- C4 One common probability calibration method on cal-A, chosen by ADR-008 from cal-A cross-validation only; use the
  currently recommended scikit-learn mechanism for fitted models (check the docs).
- C5 Repeated split seeds (3/5/10 by profile) for mean and std (development splits only; the frozen test split is untouched).
- C6 `make final` with the G6 lock: the single test-split evaluation per final configuration: full metric catalogue
  (pack 3.3), cost metrics (tuning and training time, single-row latency p50/p95, 5,000-row batch latency, model size),
  regression-track metrics for linreg, per-model metric JSON, test_predictions.csv per model, reports/v2_final.md.
- C7 Guards G3, G4, G5, G6, G7 active. Any metric >= 0.97 means: stop feature work and investigate leakage; log the finding.

### Stage D: Comparison science and evidence packet (MM-S4, pack 7.4)  (tag stage-d-built)
- D1 Paired stratified bootstrap (2,000 resamples, identical across models): 95% CIs for macro-F1, accuracy, QWK, and the
  CI of the rank-1 versus rank-2 macro-F1 difference.
- D2 McNemar on test predictions (exact binomial for small discordant counts), all 21 pairs, Holm correction.
- D3 Calibration metrics (ECE, Brier, reliability data); conformal sets per model on cal-B (alpha 0.1): coverage and set size.
- D4 Robustness (5% Gaussian noise, 10% missing features), fairness on audit-only attributes with minimum group size,
  stability across split seeds.
- D5 MCDA: five profiles, user weights, Dirichlet rank probability (5,000 draws, concentration 50), decision strength
  (clear, marginal, none) implemented exactly per pack 4.3 and unit-tested with synthetic cases; ADR-009 states the rule.
- D6 Sensitivity: `make final-variants` for linear, nonlinear, noisy_overlap; rankings, Kendall tau; sensitivity.json.
- D7 Evidence packet builder (pack 4.4): numbered facts generated from machine files only, deterministic_winner,
  decision_strength, synthetic_caveat_fact, select_facts() subsets, packet hash; comparison/*.json files; guard G8.

### Stage E: Explainability and uncertainty for seven models (MM-S5, pack 7.5)  (tag stage-e-built)
- E1 Model-agnostic: permutation importance (repeated), local ablation, counterfactual options (up to 3, actionable features
  only, cost model, validated under the explained model), stability score, performance index 0-100, conformal sets.
- E2 Native: coefficients and odds ratios, top tree levels and rule text, KNN neighbours; `explanation_type` field.
- E3 Similar-cases view for non-KNN models labelled "not how this model decided".
- E4 PCA 2D/3D fitted on scaled train data; anonymised background sample (opaque ids, at most 2,000 points).
- E5 Surface grids for every model (40x40 default, max 80x80, runtime recorded); importance matrix and Spearman agreement;
  faithfulness check per model; neutral summaries for HR and data-science audiences; personas.

### Stage F: Local LLM verdict engine (MM-S6, pack section 5 and 7.6)  (tag stage-f-built)
- F1 ml/src/epk/llm/: environment config (LLM_*), clients for `ollama` and `openai_compat` (confirm request fields in the
  runtime's current documentation), model discovery, `assert_local` guard (G10), timeouts.
- F2 SYSTEM_PROMPT, user template, VERDICT_SCHEMA (inline, no $ref), prompt_version; modes verdict, why_not, second_opinion,
  audience_rewrite, each with a small fact subset.
- F3 Validator per pack 5.4 with the full test suite (G9); orchestrator with up to 2 retries and deterministic template fallback.
- F4 Cache by sha256(packet subset + prompt_version + model + options); storage of packet hash, prompt version, model,
  options, validation history, source (llm or template).
- F5 ml/scripts/llm_eval.py with six golden packets (clear, tie, trade-off, calibration conflict, POISONED packet, missing
  data); a fake LLM for CI; real-model run recorded as "pending real model" unless a local runtime is available.
- F6 docs/LLM_SETUP.md (Ollama and OpenAI-compatible servers, model choice, hardware notes, troubleshooting).
- F7 Prompt-content scan: no employee-level keys in any prompt.

### Stage G: Artifacts v2 and model cards (MM-S7, pack 7.7)  (tag stage-g-built)
- G1 artifacts/v2 layout (pack 6.5) with MANIFEST.json (SHA-256 of every file), per-model metadata, champion.json.
- G2 Loader: key whitelist, lazy loading, hash verification before load, refusal on mismatch.
- G3 Golden-input regression tests per model.
- G4 docs/model_cards/<key>.md, docs/model_card.md (comparison), datasheet v2: GENERATED from templates with numbers read
  from machine files (no hand-typed numbers); states "rankings depend on the synthetic generator".

### Stage H: Backend API v2 (MM-S8, pack 7.8)  (tag stage-h-built)
- H1 Keep /api/v1 (default model knn); add /api/v2 per pack 6.4 (models, predict, predict/all, explain, compare/*, mcda,
  viz/surface, llm/*). Problem-details errors incl. 503 with fallback hint when the LLM is unreachable.
- H2 Integrate the REVIEWED auth/RBAC (Stage A2) on all v2 routes; stricter rate limits on /llm; no raw prompts or packets in
  logs (hashes only).
- H3 Discharge obligation O1: fix the v1 golden-test schema mismatch properly and remove the skipif.
- H4 OpenAPI v2 export, generated TypeScript types, mock server with validated and fallback sample verdicts.
- H5 Guards G11 and G12 active. predict/all p95 under 800 ms on this machine (document SVM cost).

### Stage I: Frontend foundation amendments and core pages (7.0b and MM-S9)  (tag stage-i-built)
- I1 Okabe-Ito model palette tokens, marker shapes, ModelChip, chart kit (overlay, small multiples, CI whiskers, bump chart,
  diverging scale, table views).
- I2 Predict: model selector, all-models panel (probability bars, agreement meter, split-decision flag, champion highlight),
  explanation section following the chosen model with the explanation_type badge.
- I3 What-if advisor, Batch (one model or all; per-model columns; disagreement filter; messy CSV handling; 5,000 x 7 smooth),
  Model Lab (tune any model, label "experimental, not deployed"), Dashboard, Methodology (renders model cards).
- I4 Component tests and Playwright flows (predict-all, batch with model choice, explain per model). Keep strict TypeScript.

### Stage J: Model Arena (MM-S10, pack 6.1 and 7.10)  (tag stage-j-built)
- J1 Overview (leaderboard with CI whiskers, verdict card, decision-strength badge, profile selector), Priorities (calls the
  server MCDA endpoint; no duplicate client logic), Head-to-head, Metrics deep dive, Cost and speed, Data sensitivity,
  Explainability compare, Fairness and robustness compare, dedicated LLM Verdict page.
- J2 LLM panel: headline, recommendation chip with confidence, claims with clickable fact chips, trade-offs, caveats,
  per-model "why not", audience toggle, profile selector, Regenerate, read-only evidence viewer, validation badge, runtime
  line, disagreement banner, template-fallback state. Works with no LLM.
- J3 Every chart has a table view; models distinguishable without colour; intervals wherever a rank appears.
- J4 Component and Playwright tests.

### Stage K: 3D experiences (MM-S11 and original Session 9)  (tag stage-k-built)
- K1 REQUIRED: Decision Landscape (model switcher, two-model overlay, difference surface, 2-D fallback); 3D Neighbour Explorer
  (KNN) with similar-cases view for other models; Talent Galaxy hero with Pause control.
- K2 OPTIONAL if time remains: Pipeline Story, KNN Academy, Result Reveal, Org Constellation, Drift Flow.
- K3 Quality tiers, reduced-motion, WebGL fallback, lazy loading, disposal on unmount, off-screen stop; tests for fallbacks and
  a mount/unmount leak test; docs/performance.md written from your own measurements (never invented).

### Stage L: Secure app and MLOps (MM-S12 and original Sessions 10 to 12 core)  (tag stage-l-built)
- L1 Migrations for all tables (users, employees, protected attributes, snapshots, predictions, review_items,
  review_decisions, batch_jobs, model_versions, comparison_runs, llm_verdicts, drift_reports, fairness_reports, api_keys,
  audit_logs, consent_records, deletion_requests); SQLite dev, PostgreSQL in compose.
- L2 RBAC for Admin, HR Manager, Analyst, Viewer on EVERY route including Arena and LLM; negative tests; append-only audit log.
- L3 Review workflow (uncertainty-first queue, mandatory override reasons, decision-log analytics), employee transparency page,
  appeal workflow, retention and deletion, audit explorer.
- L4 Governed retrain-all: runs the full pipeline for seven models, regenerates comparison files, evidence packet, verdict;
  proposes a champion by the ADR-009 rule; Admin approval; frozen-holdout hash unchanged; one-click rollback.
- L5 Per-model drift (PSI and KS) and performance monitoring; shadow mode = runner-up model; feature-flag admin.
- L6 PDF reports (employee report, comparison report) with disclaimer and model version.

### Stage M: Optional wave 2 (only if A to L and N are complete)
Saved views and expiring share links, scoped API keys and webhooks, i18n with one extra language, scheduled reports. Each
behind a feature flag with tests. Anything skipped is listed as SKIPPED with the reason in the build report.

### Stage N: Build-side hardening and delivery  (tag stage-n-built, then v2.0-rc)
- N1 Raise test coverage on core logic (ml and backend) to at least 80% by writing real tests; frontend component tests.
- N2 Dockerfiles (non-root, health checks), docker-compose (db, api, web), CI workflow (lint, guard, tests, build), release
  workflow; `.env.example` with dummy values only; no secrets anywhere.
- N3 Structured logs with request IDs, health and readiness endpoints, backup script.
- N4 README quick start (works with the LLM off) in 10 minutes; user guides per role; runbook; ADR index; CHANGELOG.
- N5 Demo script (5 minutes), viva Q&A sheet, final model card and datasheet v2 (generated), limitations section.
- N6 Run `make guard`, `make lint`, `make test`, `make build`, `make train PROFILE=fast` (reproducibility) and fix failures.

## 6. DECISION DEFAULTS (use these instead of asking)

Boosting: histogram gradient boosting only (others by ADR). Calibration: decided in ADR-008 from cal-A cross-validation.
Scaler: standard unless ADR-007 shows otherwise. Dev database: SQLite; compose: PostgreSQL. LLM: provider `ollama`, base URL
http://localhost:11434, model from environment or chosen by an Admin in the UI, temperature 0, seed 42, context 8192, 2
retries. Default priority profile: Balanced. Default variant: nonlinear. Frontend: React 19 + TypeScript strict + Vite,
Tailwind + shadcn/ui, TanStack Query, Zustand; 3D via R3F on stable v9.x with drei v10.x (no release candidates, no
--legacy-peer-deps). Palette and class glyphs as in the Master Build Prompt. Licence: keep the existing one. Anything not
covered: choose the more conservative, more secure, more reversible option and log it.

## 7. DONE DEFINITION AND FINAL REPORT

The build is COMPLETE when: every checklist item in docs/BUILD_PROGRESS.md is done or marked SKIPPED with a reason (only
Stage M and K2 may be skipped); `make guard`, `make lint`, `make test`, `make build` pass; `make train PROFILE=fast` reproduces
the same metrics twice; the app starts with `make dev` and `make seed` (development credentials only); the working tree is
clean; v2.0-rc is tagged.

Write docs/BUILD_REPORT.md with: what was built per stage; decisions (link DECISIONS_LOG.md); deviations; deferred items
(real-LLM golden evaluation, all human checks, anything marked "pending real model"); known issues; headline numbers read
from machine files WITH their file paths; commit and tag list; an explicit sentence "No verification checks have been
executed or claimed in this report." Then print a final summary (at most 40 lines) ending with: "BUILD COMPLETE. Next step:
run the verification prompt in a fresh session."

## 8. START NOW

1. Read docs/STATE.md, docs/BUILD_PROGRESS.md (if it exists), docs/MULTIMODEL_PACK.md (Parts 2 to 6 and 10), the Master
   Build Prompt and the Addendum. Run `git status`, `git log --oneline -n 15`.
2. If the tree is dirty with changes you did not make, hard stop (rule 2d). Otherwise create docs/BUILD_PROGRESS.md and begin
   Stage A. Do not ask me anything. Work through the stages in order.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-10-12T18:24:03+05:30.

The user's current state is as follows:
Active Document: c:\Users\resma\Documents\WORKSHOP\DM-CBP\.gitignore (LANGUAGE_UNSPECIFIED)
Cursor is on line: 1
Other open documents:
- c:\Users\resma\Documents\WORKSHOP\DM-CBP\ml\scripts\variant_check.py (LANGUAGE_PYTHON)
- c:\Users\resma\Documents\WORKSHOP\DM-CBP\ml\configs\schema.yaml (LANGUAGE_YAML)
- c:\Users\resma\Documents\WORKSHOP\DM-CBP\docs\data_dictionary.md (LANGUAGE_MARKDOWN)
- c:\Users\resma\Documents\WORKSHOP\DM-CBP\.gitignore (LANGUAGE_UNSPECIFIED)
- c:\Users\resma\Documents\WORKSHOP\DM-CBP\docs\01-spec.md (LANGUAGE_MARKDOWN)

The user has mentioned some items in the form @[ITEM]. Here is extra information about the items that were mentioned by the user, in the order that they appear:

/plan is a [Slash Command]:
<PLAN>The user is requesting that you think and plan carefully before executing the upcoming task.
Carefully research the task, make sure that you and the user are aligned on the goals and requirements,
create a detailed implementation plan artifact, and get user approval on the plan before making any code changes (besides artifacts)
or running any modifying commands.

# Guidelines
- Establish a shared understanding of the task with the user. If there are any ambiguities, underspecified requirements,
or implicit assumptions, clarify them with the user before proceeding.
- Thoroughly research the codebase to establish a solid understanding of the relevant components, systems, dependencies, and architecture.
As you research, provide verbal updates of your research steps and thought process with the user, so they can follow along.
- Create an implementation plan artifact that outlines your proposed execution strategy.
Set request_feedback = true and user_facing = true in the ArtifactMetadata. The user will automatically
see any new and modified plans you create, so DO NOT re-summarize the plan.
- Only after the user explicitly approves the plan should you proceed to execution.
- Verify that your changes have the desired effects e.g. run unit tests, make sure code builds, etc. before claiming that the task is complete.
- After you've completed your task and verified that your solution works, create a walkthrough artifact to summarize your work.

# Planning Mode Artifacts
When in planning mode, you should create two special artifacts.

# Implementation Plan
Path: <Artifact Directory>/<plan_name>.md

**Purpose**: A technical design document to present your implementation plan to the user for feedback and approval.
After reading the document, the user should understand the key technical details of your plan, and be able to make an informed decision on whether to approve it.
This document should be very detailed, including code snippets, diffs, mermaid diagrams, verification strategies, and background information.

**Format**: Use the following format, omitting any irrelevant sections:

## [Goal Description]
Provide a brief description of the problem, any background context, and what the change accomplishes.

## User Review Required
Document anything that requires user review or feedback, for example, breaking changes or significant design decisions. Use GitHub alerts (IMPORTANT/WARNING/CAUTION) to highlight critical items.

## Open Questions
Any clarifying or design questions for the user that will impact the implementation plan. Use GitHub alerts (IMPORTANT/WARNING/CAUTION) to highlight critical items.

## Proposed Changes
Group files by component (e.g., package, feature area, dependency layer) and order logically (dependencies first). Separate components with horizontal rules for visual clarity.

### [Component Name]
Summary of what will change in this component with explicit code snippets and diffs. For specific files, Use [NEW] and [DELETE] to demarcate new and deleted files, for example:
#### [MODIFY] file basename
#### [NEW] file basename
#### [DELETE] file basename

## Verification Plan
Summary of how you will verify that your changes have the desired effects.

### Automated Tests
Exact commands to run automated tests

### Manual Verification
Instructions for what the user should manually verify.

# Walkthrough
Path: <Artifact Directory>/walkthrough.md

**Purpose**: After completing work, summarize what you accomplished. Update an existing walkthrough for related follow-up work rather than creating a new one.

**Document**:
- Changes made
- What was tested
- Validation results

Embed screenshots and recordings to visually demonstrate UI changes and user flows.</PLAN>
/build-app is a [Slash Command]:
<SKILL>The user requested you read and use the "build-app" skill. The path to the skill file is:
C:\Users\resma\.gemini\config\skills\build-app\SKILL.md</SKILL>
/zero-to-deploy is a [Slash Command]:
<SKILL>The user requested you read and use the "zero-to-deploy" skill. The path to the skill file is:
C:\Users\resma\.gemini\config\skills\zero-to-deploy\SKILL.md</SKILL>
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from Gemini 3.1 Pro (High) to Claude Opus 4.6 (Thinking). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>