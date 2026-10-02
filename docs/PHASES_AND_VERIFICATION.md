# TalentScope: Complete Phases Plan with Verification Gates

**Every phase from foundations to final release, with measurable verification checks, evidence rules and an end-of-project review protocol**

*Version of 2 October 2026. Companion file: `VERIFICATION_LOG.md` (the living evidence record that you fill in as you go and send back at the end).*

---

## 1. Purpose and How the Pieces Fit

| Document | Role |
|---|---|
| **This document (PLAN)** | The authoritative list of phases, release tags and **verification checks (IDs `V0.1`, `V1.3`, …)** with pass thresholds. Defines what "done" means for each phase |
| **`VERIFICATION_LOG.md` (LOG)** | A living record, one block per phase, with a row for every check ID. Copy it into the repo at `docs/VERIFICATION_LOG.md`. You and the coding agent fill it in; you send it (plus an evidence bundle) for the final review |
| **Session prompts (earlier document, Part 7)** | The paste-ready build instructions for the coding agent, Session 0 to Session 14 |
| **Project report and build-phases plan (earlier documents)** | Method detail: data mining theory, schema, UI/UX blueprint, API contracts |

**Precedence rule:** if the session prompt and this document differ on *what to build*, the session prompt wins. If they differ on *what counts as done*, **the stricter standard wins**.

**Phase numbering:** Phase N in this document = Session N in the session prompts. Phase 15 is new: the final review and handover.

## 2. The Loop for Every Phase

```
1. Paste the Session prompt  +  the Verification Addendum (Appendix A)
2. Agent builds, runs every check marked A or B, and fills the LOG block with RAW outputs
3. You run every check marked H or B (about 5 minutes each; 20 to 45 minutes per phase)
4. Mark the gate: PASS / PASS with waiver / FAIL (rules in section 3.5)
5. Commit the LOG and the evidence folder, tag the release, then start the next phase
```

| Marker | Meaning |
|---|---|
| **A** | The agent runs it and pastes raw output into the LOG |
| **H** | **You** run it yourself (independent check; this is what makes the process trustworthy) |
| **B** | Both run it; compare the two results |
