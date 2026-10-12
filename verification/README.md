# Independent Verification Suite

This directory contains standalone, independent verification scripts written by the independent verification engineer.
Per Verification Rule 5:
- Scripts import ONLY standard numerical libraries (`numpy`, `pandas`, `scipy`, `scikit-learn`, `hashlib`, `json`).
- Scripts DO NOT import internal project code (`epk.*`, `backend.*`) for metric replications.
- All metrics, bootstrap intervals, McNemar tests, conformal sets, and MCDA rankings are recomputed directly from raw files.

## Scripts Index
- `x01_leakage_mutation.py`: Adversarial mutation test (X1, VM2.3)
- `x02_generator_freeze.py`: Adversarial generator modification test (X2, VM1.10)
- `x03_test_once.py`: Adversarial test-set-once re-evaluation refusal test (X3, VM3.2)
- `x04_tamper_detection.py`: Adversarial single-byte corruption attack (X4, VM7.2)
- `x05_validator_attacks.py`: 10 synthetic adversarial invalid LLM verdicts + 3 faithful (X5, VM6.5)
- `x06_prompt_injection.py`: Adversarial prompt injection resistance check (X6, VM6.7)
- `x07_llm_fallback.py`: LLM unavailable graceful degradation test (X7, VM6.9)
- `x08_rbac_matrix.py`: Full OpenAPI route-by-role security matrix generator & test (X8, V10.4, VM12.1)
- `x09_auth_abuse.py`: Brute force, expired JWT, 'alg none' forgery attack tests (X9, V10.2)
- `x10_csv_sanitization.py`: Formula injection (=, +, -, @) & oversized CSV attack (X10, V6.7)
- `x11_model_key_traversal.py`: Path traversal attack on model parameters (X11, VM8.9)
- `x12_llm_ssrf.py`: Local loopback vs public/link-local SSRF guard attack (X12, VM6.2)
- `x13_privacy_scan.py`: Zero employee-level / protected attribute scanner (X13, VM6.3, V9.11)
- `x14_reproducibility.py`: Training determinism and manifest comparison (X14, VM3.8, VM7.4)
- `x15_label_order_trap.py`: Invariance to class probability order [0, 1, 2] (X15, VM2.4)
- `x16_independent_metrics.py`: Independent recomputation of Accuracy, Macro-F1, QWK, Bootstrap CIs, McNemar (X16, VM3, VM4.1, VM4.2)
- `x17_independent_mcda.py`: Independent replication of 5 MCDA profile ranks & Dirichlet probs (X17, VM4.4, VM4.5)
- `x18_independent_conformal.py`: Independent recomputation of conformal coverage on test set (X18, VM4.8)
- `x19_independent_train_replication.py`: Independent training of LogReg & RF from raw data (X19, VM3.9)
- `x20_knn_by_hand.py`: Manual Euclidean distance verification for KNN exemplars (X20, VM5.3)
- `x21_surface_cells.py`: 5 random 2D grid cells vs predict_proba verification (X21, VM11.1)
- `x22_perf_benchmarks.py`: API latency p50/p95 and 5,000-row batch timings (X22, VM8.4, V13.3)
- `x24_security_tooling.py`: Automated dependency audit, bandit, and git secret regex scan (X24, V13.4-13.7)
- `x25_docker_drill.py`: Docker Compose config, build, and health check validation (X25, V14.x)
- `x26_numbers_consistency.py`: Cross-document number consistency scanner against machine files (X26, V15.3, VM7.5)
