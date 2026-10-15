"""Kopiert die kanonische SKILL.md in die Spiegel für Claude und Codex."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "mailbox-triage" / "SKILL.md"
DESTINATIONS = (
    ROOT / ".claude" / "skills" / "mailbox-triage" / "SKILL.md",
    ROOT / ".agents" / "skills" / "mailbox-triage" / "SKILL.md",
)


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    text = SOURCE.read_text(encoding="utf-8")
    if "--check" in args:
        for dest in DESTINATIONS:
            if not dest.is_file() or dest.read_text(encoding="utf-8") != text:
                print(f"weicht ab: {dest}", file=sys.stderr)
                return 1
        return 0
    for dest in DESTINATIONS:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
