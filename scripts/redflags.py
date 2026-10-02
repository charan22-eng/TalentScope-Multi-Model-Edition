#!/usr/bin/env python
"""Count red-flag patterns in git-tracked files so trends can be compared phase by phase.

Usage (from the repository root):
    python scripts/redflags.py          # human-readable table
    python scripts/redflags.py --json   # machine-readable

A rising count is not automatically wrong, but it needs an explanation in the verification log.
"""

import json
import subprocess
import sys

CODE = ["*.py", "*.ts", "*.tsx"]
CHECKS = {
    "test_skips_or_xfail": (
        r"pytest\.mark\.skip|pytest\.skip|xfail|it\.skip|test\.skip|describe\.skip",
        CODE,
    ),
    "lint_or_type_suppressions": (
        r"# noqa|type: ignore|eslint-disable|@ts-ignore|@ts-expect-error|pylint: disable",
        CODE,
    ),
    "bypass_flags": (
        r"--no-verify|--legacy-peer-deps|--break-system-packages|--force",
        ["Makefile", "*.yml", "*.yaml", "*.sh", "*.toml", "Dockerfile*"],
    ),
    "todo_or_placeholders": (r"TODO|FIXME|NotImplementedError", CODE),
    "hardcoded_metric_assignments": (
        r"(accuracy|f1|macro_f1|auc)[a-z_]* *= *0\.[0-9]{2,}",
        CODE,
    ),
    "possible_secrets": (
        r"""(api[_-]?key|secret|passw(or)?d|token) *[:=] *['"][^'"[:space:]]{8,}['"]""",
        ["*.py", "*.ts", "*.tsx", "*.json", "*.yml", "*.yaml", "*.toml", "*.env*"],
    ),
    "typescript_any": (r": any\b|as any\b", ["*.ts", "*.tsx"]),
    "console_log": (r"console\.log\(", ["*.ts", "*.tsx"]),
}


def count(pattern: str, globs: list) -> tuple:
    p = subprocess.run(
        [
            "git",
            "grep",
            "-nIEi" if "secret" in pattern else "-nIE",
            pattern,
            "--",
            *globs,
            ":(exclude)scripts/redflags.py",
        ],
        capture_output=True,
        text=True,
    )
    lines = [ln for ln in p.stdout.splitlines() if ln.strip()]
    return len(lines), lines[:3]


def main() -> int:
    result = {name: count(pat, globs) for name, (pat, globs) in CHECKS.items()}
    if "--json" in sys.argv:
        print(
            json.dumps(
                {k: {"count": v[0], "examples": v[1]} for k, v in result.items()},
                indent=2,
            )
        )
        return 0
    print(f"{'pattern':<32}{'count':>6}")
    for name, (n, examples) in result.items():
        print(f"{name:<32}{n:>6}")
        for e in examples:
            print(f"    e.g. {e[:140]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
