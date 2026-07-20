"""Block a commit that deletes more than LIMIT lines, unless ALLOW_BIG_DELETE=1.

A brake against the agent silently gutting working code.

Port of scripts/deletion-guard.mjs from agentic-harness@3226f96 (ts-base template),
rewritten in Python so a Python repo needs no node toolchain. Deliberate, stamped
divergence (ADR 9); the limit and the escape hatch are unchanged.
"""

import os
import subprocess
import sys

LIMIT = 80


def main() -> int:
    diff = subprocess.run(
        ["git", "diff", "--cached", "--numstat"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    deleted = 0
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        _added, removed, _path = parts[0], parts[1], parts[2]
        if removed == "-":  # binary file
            continue
        deleted += int(removed)

    if deleted > LIMIT and os.environ.get("ALLOW_BIG_DELETE") != "1":
        print(
            f"X Deletion guard: {deleted} lines deleted (limit {LIMIT}).\n"
            f"  Set ALLOW_BIG_DELETE=1 if this is intentional.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
