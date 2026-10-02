#!/usr/bin/env python
"""Build the end-of-project review bundle (zip) for independent review.

Usage (from the repository root):
    python scripts/build_review_bundle.py [--out reports/review_bundle.zip] [--allow-warnings]

Includes: docs/, reports/ (incl. evidence), key artifact metadata, lock files, CI config, openapi.json,
coverage/junit summaries. Excludes: raw data, model binaries, node_modules, virtualenvs, .env files, files > 25 MB.
Scans included text files for likely secrets; refuses to build when any are found unless --allow-warnings is set.
A MANIFEST.json with SHA-256 hashes of every included file is written into the zip.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

INCLUDE_DIRS = ("docs", "reports")
INCLUDE_FILES = {
    "README.md",
    "Makefile",
    "uv.lock",
    "docker-compose.yml",
    "frontend/package.json",
    "frontend/package-lock.json",
    "data/manifest.json",
    "artifacts/v1/metadata.json",
    "artifacts/v1/comparison.json",
    "artifacts/v1/conformal.json",
    "artifacts/v1/importance.json",
    ".github/workflows/ci.yml",
}
INCLUDE_NAMES = {"openapi.json", "coverage.xml", "coverage-summary.json", "junit.xml"}
EXCLUDE_DIRS = {
    "node_modules",
    ".venv",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".pytest_cache",
    ".ruff_cache",
}
EXCLUDE_NAMES = {".env"}
SKIP_SCAN_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".mp4",
    ".webm",
}
MAX_BYTES = 25 * 1024 * 1024
SECRET_RE = re.compile(
    r"""(?i)(api[_-]?key|secret|passw(or)?d|token|private[_-]?key)\s*[:=]\s*['"][^'"\s]{8,}['"]"""
)


def walk(root: str = "."):
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
        for f in files:
            yield Path(d) / f


def wanted(p: Path) -> bool:
    posix = p.as_posix().lstrip("./")
    if p.name in EXCLUDE_NAMES or p.name.startswith(".env."):
        # .env.example is allowed (dummy values only); real env files never
        return p.name == ".env.example"
    if p.stat().st_size > MAX_BYTES:
        return False
    if posix in INCLUDE_FILES or p.name in INCLUDE_NAMES:
        return True
    return any(posix == d or posix.startswith(d + "/") for d in INCLUDE_DIRS)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(cmd: str) -> str:
    try:
        return subprocess.run(
            cmd, shell=True, capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/review_bundle.zip")
    ap.add_argument("--allow-warnings", action="store_true")
    a = ap.parse_args()

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    files = [
        p for p in walk() if p.is_file() and p.resolve() != out.resolve() and wanted(p)
    ]

    warnings = []
    for p in files:
        if p.suffix.lower() in SKIP_SCAN_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in SECRET_RE.finditer(text):
            warnings.append(
                f"{p.as_posix()}: possible secret near '{m.group(0)[:40]}...'"
            )

    if warnings and not a.allow_warnings:
        print("[bundle] REFUSING to build: possible secrets found")
        for w in warnings:
            print("  -", w)
        print("Fix them (or re-run with --allow-warnings after manual review).")
        return 2

    manifest = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git("git rev-parse HEAD"),
        "git_remote": git("git remote -v"),
        "git_tag": git("git describe --tags --always"),
        "working_tree_clean": git("git status --porcelain") == "",
        "secret_scan_warnings": warnings,
        "files": {p.as_posix(): sha256(p) for p in files},
    }
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.as_posix())
        z.writestr("MANIFEST.json", json.dumps(manifest, indent=2))
    print(
        f"[bundle] wrote {out} with {len(files)} files; secret warnings: {len(warnings)}"
    )
    print(
        f"[bundle] git sha: {manifest['git_sha'] or 'UNKNOWN'}  clean tree: {manifest['working_tree_clean']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
