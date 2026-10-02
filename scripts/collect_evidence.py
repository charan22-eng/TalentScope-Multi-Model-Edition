#!/usr/bin/env python
"""Collect verification evidence for one phase.

Usage (run from the repository root):
    python scripts/collect_evidence.py --phase 3 \
        --cmd "tests::uv run pytest ml/tests -q" \
        --cmd "train::make train" \
        --files data/manifest.json artifacts/v1/metadata.json

Each --cmd is "label::command". Output goes to reports/evidence/phase-<N>/evidence.json and contains:
git SHA, working-tree cleanliness, remote URL, tool versions, the raw stdout/stderr tail of every
command, exit codes, run time, and SHA-256 hashes of any --files. Exit code is 1 if any command failed.
Raw output is evidence; a summary written by a person or an AI agent is not.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path


def run(cmd: str, timeout: int = 3600) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", f"TIMEOUT after {timeout}s"
    return {
        "cmd": cmd,
        "returncode": rc,
        "seconds": round(time.time() - t0, 2),
        "stdout_tail": out[-20000:],
        "stderr_tail": err[-8000:],
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, help="phase number, e.g. 3")
    ap.add_argument(
        "--cmd", action="append", default=[], help='"label::command" (repeatable)'
    )
    ap.add_argument("--files", nargs="*", default=[], help="files to hash and record")
    ap.add_argument(
        "--note", default="", help="free-text note stored with the evidence"
    )
    a = ap.parse_args()

    out_dir = Path("reports") / "evidence" / f"phase-{a.phase}"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "phase": a.phase,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_toplevel": run("git rev-parse --show-toplevel")["stdout_tail"].strip(),
        "git_sha": run("git rev-parse HEAD")["stdout_tail"].strip(),
        "git_branch": run("git rev-parse --abbrev-ref HEAD")["stdout_tail"].strip(),
        "git_working_tree_clean": run("git status --porcelain")["stdout_tail"].strip()
        == "",
        "git_remote": run("git remote -v")["stdout_tail"].strip(),
        "note": a.note,
    }

    results = []
    for item in a.cmd:
        label, sep, cmd = item.partition("::")
        if not sep:
            label, cmd = "cmd", item
        r = run(cmd)
        r["label"] = label
        results.append(r)

    hashes = {f: sha256(Path(f)) for f in a.files if Path(f).is_file()}
    missing = [f for f in a.files if not Path(f).is_file()]

    payload = {
        "meta": meta,
        "results": results,
        "hashes": hashes,
        "missing_files": missing,
    }
    (out_dir / "evidence.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    failed = [r["label"] for r in results if r["returncode"] != 0]
    print(f"[evidence] wrote {out_dir / 'evidence.json'}")
    print(
        f"[evidence] commands: {len(results)}  failed: {failed or 'none'}  missing files: {missing or 'none'}"
    )
    print(
        f"[evidence] git sha: {meta['git_sha'] or 'UNKNOWN'}  clean tree: {meta['git_working_tree_clean']}"
    )
    return 1 if (failed or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
