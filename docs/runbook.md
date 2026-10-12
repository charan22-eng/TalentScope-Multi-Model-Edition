# TalentScope Operations Runbook

## 1. System Overview & Health Monitoring
TalentScope provides automated health and readiness probes:
- Liveness Probe: `GET /health` -> Returns `{"status": "ok"}`
- Readiness Probe: `GET /ready` -> Validates active database connectivity and cryptographic presence of `artifacts/v2/champion.json`.
- Prometheus / Structured Logs: All requests emit JSON-formatted logs with unique UUID `req_id`, latency in milliseconds, method, route, and status code.

## 2. Invariant Guards (`make guard` / `scripts/guard.py`)
Run the guard suite immediately whenever configuration or models change:
```bash
python scripts/guard.py
```
If any guard fails:
- **G1 (Generator Frozen)**: `ml/src/epk/data.py` has been modified. Revert changes to maintain data reproducibility.
- **G2 (Target/Protected Isolation)**: A protected column (gender, age_band, ethnicity) was detected in features. Remove from `ml/configs/schema.yaml`.
- **G3 (Ordered Labels)**: A model produced labels other than `[0, 1, 2]`. Verify label encoding in `epk.labels`.
- **G5 (Split Frozen)**: `data/processed/split.json` hash changed. Restore frozen split file.
- **G6 (Test Lock)**: Evaluation occurred on test holdout without lock configuration. Revert to cross-validation or calibration splits.
- **G11 (Whitelist/Traversal)**: An invalid model key was requested or path traversal attempt blocked.

## 3. Incident Response: Feature Drift Alert
When `GET /api/v2/drift/status` returns `status: "significant_drift"` (overall PSI >= 0.25):
1. **Identify Drifting Features**: Inspect `features` map in the drift report to identify which numerical features have PSI > 0.25 (e.g. `attendance`, `projects_completed`).
2. **Review Data Source**: Verify whether recent data ingest includes changes in reporting cycles, seasonal holidays, or batch logging formats.
3. **Trigger Governed Retrain Pipeline**:
   - Access Admin console or call `POST /api/v2/retrain` with `profile="standard"`.
   - Pipeline trains all 7 candidate models and generates new candidate metrics.
   - Verify candidate evaluation against frozen holdout.
   - Admin approves new champion via `POST /api/v2/models/approve-champion`.

## 4. Emergency Champion Rollback Procedure
If the active model champion displays unexpected behavior in production:
1. Trigger one-click rollback via API:
   ```bash
   curl -X POST http://localhost:8000/api/v2/models/rollback \
     -H "Authorization: Bearer <ADMIN_TOKEN>"
   ```
2. The system restores `rf` (Random Forest v2.0 baseline), re-hashes `artifacts/v2/champion.json`, updates `MANIFEST.json`, and records an immutable audit log.
3. Validate rollback via `GET /api/v2/models` to confirm `is_champion: true` on `rf`.

## 5. Backup & Disaster Recovery
### Automated Backup
Run daily via cron / scheduler:
```bash
python scripts/backup.py
```
This generates a verified archive in `backups/talentscope_backup_<TIMESTAMP>.zip` and computes a SHA-256 integrity hash in the accompanying `.json` file.

### Restoration Procedure
To restore from a backup:
1. Stop backend service: `docker compose stop backend`
2. Extract zip contents into project root:
   ```bash
   unzip backups/talentscope_backup_<TIMESTAMP>.zip -d .
   ```
3. Run migrations and verify table integrity:
   ```bash
   python backend/db/migrate.py
   python scripts/guard.py
   ```
4. Restart services: `docker compose start backend`
