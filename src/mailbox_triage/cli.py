"""Befehle classify und schema. classify schreibt nur den Report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mailbox_triage.parse import load_path
from mailbox_triage.report import schema_payload, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mailbox-triage")
    sub = parser.add_subparsers(dest="cmd", required=True)

    classify = sub.add_parser("classify", help="Lokalen Export sortieren")
    classify.add_argument("pfad", type=Path)
    classify.add_argument("--out", required=True, type=Path, help="Markdown-Report, JSON daneben")

    sub.add_parser("schema", help="Klassen und Felder auf stdout")

    args = parser.parse_args(argv)
    if args.cmd == "schema":
        json.dump(schema_payload(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    path: Path = args.pfad
    if not path.exists():
        print(f"Pfad fehlt: {path}", file=sys.stderr)
        return 2
    if path.is_file() and path.suffix.lower() not in {".eml", ".mbox"}:
        print("Nur .eml, .mbox oder ein Ordner.", file=sys.stderr)
        return 2
    try:
        rows = load_path(path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_report(rows, str(path), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
