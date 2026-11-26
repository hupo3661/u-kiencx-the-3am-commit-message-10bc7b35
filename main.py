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

The entry line itself is frozen text: it is validated and written
byte-for-byte, never normalised, trimmed, or re-wrapped. What this
program adds around it is a small, strict pipeline -- validate, write
atomically, then read the file back and prove it matches -- so a bad
entry fails here instead of at the grading gate.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Frozen entry text. Do not edit: the graded line, character for character.
LINE = "fix: fixed my own bug, then fixed the fix, then apologized to the fix. it works now, do not ask."

DEFAULT_OUTPUT = "/output/entry.txt"


@dataclass(frozen=True)
class EntryConfig:
    """Everything the pipeline needs, in one immutable place."""

    line: str
    max_chars: int = 139
    default_output: str = DEFAULT_OUTPUT

    @property
    def expected_bytes(self) -> bytes:
        return self.line.encode("utf-8")

    @property
    def expected_sha256(self) -> str:
        return hashlib.sha256(self.expected_bytes).hexdigest()


CONFIG = EntryConfig(line=LINE)


class EntryError(Exception):
    """The entry or the output file failed a check; exit non-zero."""


def validate(config: EntryConfig) -> None:
    """Reject any entry the grading gate would refuse, with a reason."""
    line = config.line
    problems: list[str] = []
    if not line.strip():
        problems.append("entry line is empty")
    if len(line) > config.max_chars:
        problems.append(
            f"entry line is {len(line)} chars, over the "
            f"{config.max_chars}-char limit"
        )
    if "\n" in line or "\r" in line:
        problems.append("entry line must be a single line")
    if line != line.strip():
        problems.append("entry line has leading or trailing whitespace")
    if problems:
        raise EntryError("; ".join(problems))


def resolve_output(cli_output: str | None) -> Path:
    """CLI flag wins, then OUTPUT_PATH, then the graded default."""
    raw = cli_output or os.environ.get("OUTPUT_PATH") or CONFIG.default_output
    return Path(raw).expanduser()


def write_entry_atomic(config: EntryConfig, target: Path) -> Path:
    """Write the line atomically: temp file in the same dir, then rename.

    A half-written entry.txt is worse than no entry.txt, so the bytes
    only ever appear at the target path once they are complete.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=target.name + ".", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(config.expected_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
    return target


def verify_written(config: EntryConfig, target: Path) -> None:
    """Read the file back and prove it is the entry, byte for byte."""
    actual = target.read_bytes()
    if actual != config.expected_bytes:
        raise EntryError(
            f"verification failed: {target} holds {len(actual)} bytes, "
            f"expected {len(config.expected_bytes)} bytes "
            f"(sha256 {hashlib.sha256(actual).hexdigest()[:12]}... "
            f"!= {config.expected_sha256[:12]}...)"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write the 3AM Commit Message entry to entry.txt."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="destination file (default: $OUTPUT_PATH or /output/entry.txt)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate(CONFIG)
        target = resolve_output(args.output)
        write_entry_atomic(CONFIG, target)
        verify_written(CONFIG, target)
    except EntryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: cannot write entry: {exc}", file=sys.stderr)
        return 1
    print(CONFIG.line)
    print(
        f"wrote {len(CONFIG.line)} chars to {target} "
        f"(sha256 {CONFIG.expected_sha256[:12]}...)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
