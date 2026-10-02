# Risks Log

| Risk | Likelihood | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| Synthetic data too easy (near-perfect scores) | Medium | High | Noise/overlap tuning in 2.3; external validation set (2.6) | DME | Open |
| Data leakage inflates metrics | Medium | High | Pipelines only, leakage tests (4.8), frozen test set (5.1) | DMR | Open |
| Scope creep in Phase 15 | High | Medium | Feature flags, priority order, freeze at week 10 | PM/all | Open |
| Frontend blocked by backend delay | Medium | Medium | OpenAPI-first, mock server (11.10) | BE/FE | Open |
| Demo-day failure | Low | High | Pre-recorded video, Streamlit fallback (5.5), staging URL | QA | Open |
| Insecure model loading | Low | High | Load only self-produced artifacts; hash verification (10.3) | AIE | Open |
| Fairness or ethics criticism | Medium | Medium | Phase 9 audit, model card, human-review policy | DMR | Open |
| Key member unavailable | Medium | Medium | Pairing, code review, cross-training, docs | All | Open |
| Deployment cost or limit surprises | Low | Medium | Verify current pricing/limits early (17.5) | QA | Open |
