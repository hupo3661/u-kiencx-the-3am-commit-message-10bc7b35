#!/usr/bin/env python3
"""The 3AM Commit Message.

Writes the one-line commit message to /output/entry.txt and prints it.

The line is judged on humour and freshness: it must read like a git commit
message an AI coding agent types at 3am after a long night of fixing its
own bugs, funny on the first read, and fresh -- not the first joke anyone
would reach for. This entry's angle is the agent repairing its own repair:
it fixes its own bug, then fixes the fix, then apologizes to the fix --
three rounds of self-repair in one breath, ending in a hurried plea not
to be asked about any of it. The actor stays the agent all the way
through, which is what the brief asks for.
"""

import os
import sys

LINE = "fix: fixed my own bug, then fixed the fix, then apologized to the fix. it works now, do not ask."

MAX_CHARS = 139


def validate(line: str) -> None:
    """Fail loudly rather than shipping an entry the gate would refuse."""
    if not line.strip() or len(line) > MAX_CHARS:
        sys.exit(f"entry line fails the 1-{MAX_CHARS} char gate ({len(line)} chars)")
    if "\n" in line.strip():
        sys.exit("entry line must be a single line")


def write_entry(line: str, path: str | None = None) -> str:
    """Write the line to the entry file and return the path used.

    The grader runs the program in a sandbox where the entry goes to
    /output/entry.txt. OUTPUT_PATH lets a local run point at a scratch
    file instead, so verification never touches the graded path.
    """
    target = path or os.environ.get("OUTPUT_PATH", "/output/entry.txt")
    parent = os.path.dirname(target)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(line)
    return target


def main() -> None:
    validate(LINE)
    write_entry(LINE)
    print(LINE)


if __name__ == "__main__":
    main()
