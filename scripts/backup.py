#!/usr/bin/env python
"""TalentScope Backup Script (Stage N3).

Generates timestamped cryptographic backup archives of database state,
configuration, and model artifacts into backups/ directory.
"""

import hashlib
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = ROOT / "backups"


def create_backup() -> Path:
    """Create a verified zip backup of database and artifacts."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    zip_path = BACKUPS_DIR / f"talentscope_backup_{ts}.zip"

    files_backed_up = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Back up database if sqlite
        db_file = ROOT / "hr_insights.db"
        if db_file.exists():
            zf.write(db_file, arcname="db/hr_insights.db")
            files_backed_up.append("hr_insights.db")

        # 2. Back up model artifacts v2
        artifacts_dir = ROOT / "artifacts" / "v2"
        if artifacts_dir.exists():
            for root, _, files in os.walk(artifacts_dir):
                for f in files:
                    full_p = Path(root) / f
                    rel_p = full_p.relative_to(ROOT)
                    zf.write(full_p, arcname=str(rel_p))
                    files_backed_up.append(str(rel_p))

        # 3. Back up configuration schema & split
        schema_file = ROOT / "ml" / "configs" / "schema.yaml"
        if schema_file.exists():
            zf.write(schema_file, arcname="config/schema.yaml")
            files_backed_up.append("schema.yaml")

        split_file = ROOT / "data" / "processed" / "split.json"
        if split_file.exists():
            zf.write(split_file, arcname="data/split.json")
            files_backed_up.append("split.json")

    # Compute SHA-256
    h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    meta_path = BACKUPS_DIR / f"talentscope_backup_{ts}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "backup_archive": zip_path.name,
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sha256": h,
                "size_bytes": zip_path.stat().st_size,
                "files_count": len(files_backed_up),
            },
            f,
            indent=2,
        )

    print(f"[OK] Backup created: {zip_path.name} ({zip_path.stat().st_size / 1024:.1f} KB, SHA-256: {h[:12]}...)")
    return zip_path


if __name__ == "__main__":
    create_backup()
