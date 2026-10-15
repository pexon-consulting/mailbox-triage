"""Kopiert die kanonische SKILL.md in die Spiegel für Claude und Codex."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "mailbox-triage" / "SKILL.md"
DESTINATIONS = (
    ROOT / ".claude" / "skills" / "mailbox-triage" / "SKILL.md",
    ROOT / ".agents" / "skills" / "mailbox-triage" / "SKILL.md",
)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for dest in DESTINATIONS:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
