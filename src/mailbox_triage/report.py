"""Markdown-Tabelle und JSON. Schreibt nur diese beiden Dateien."""

from __future__ import annotations

import json
from pathlib import Path

from mailbox_triage.parse import Zeile

COLUMNS = (
    "datei",
    "klasse",
    "sicherheit",
    "absender",
    "betreff",
    "datum",
    "rechnungsnummer",
    "betrag",
    "waehrung",
    "anhaenge",
)

HEADERS = (
    "Datei",
    "Klasse",
    "Sicherheit",
    "Absender",
    "Betreff",
    "Datum",
    "Rechnungsnummer",
    "Betrag",
    "Währung",
    "Anhänge",
)


def write_report(rows: list[Zeile], quelle: str, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(rows), encoding="utf-8")
    json_path = out.with_suffix(".json")
    json_path.write_text(render_json(rows, quelle), encoding="utf-8")
    return json_path


def render_markdown(rows: list[Zeile]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.klasse] = counts.get(row.klasse, 0) + 1
    lines = [
        "# Mailbox Triage",
        "",
        "| Klasse | Anzahl |",
        "| --- | ---: |",
    ]
    for name in ("rechnung", "mahnung", "angebot", "auftrag", "sonstiges"):
        if name in counts:
            lines.append(f"| {name} | {counts[name]} |")
    lines.extend(
        [
            "",
            "## Zeilen",
            "",
            "| " + " | ".join(HEADERS) + " |",
            "| " + " | ".join("---" for _ in HEADERS) + " |",
        ]
    )
    for row in rows:
        values = [
            row.datei,
            row.klasse,
            row.sicherheit,
            row.absender or "",
            row.betreff or "",
            row.datum or "",
            row.rechnungsnummer or "",
            row.betrag or "",
            row.waehrung or "",
            ", ".join(row.anhaenge),
        ]
        lines.append("| " + " | ".join(_cell(value) for value in values) + " |")
    lines.append("")
    return "\n".join(lines)


def render_json(rows: list[Zeile], quelle: str) -> str:
    payload = {
        "quelle": quelle,
        "zeilen": [
            {
                "datei": row.datei,
                "klasse": row.klasse,
                "sicherheit": row.sicherheit,
                "absender": row.absender,
                "betreff": row.betreff,
                "datum": row.datum,
                "rechnungsnummer": row.rechnungsnummer,
                "betrag": row.betrag,
                "waehrung": row.waehrung,
                "anhaenge": list(row.anhaenge),
            }
            for row in rows
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def schema_payload() -> dict:
    from mailbox_triage.classify import KEYWORDS, MARGIN, ORDER, THRESHOLD

    return {
        "klassen": [*ORDER, "sonstiges"],
        "schwelle": THRESHOLD,
        "vorsprung": MARGIN,
        "betreff_punkte": 3,
        "text_punkte": 1,
        "stichworte": {name: list(KEYWORDS[name]) for name in ORDER},
        "felder": list(COLUMNS),
        "schreibt_nicht": ["imap", "sap", "datev", "abas"],
    }


def _cell(value: str) -> str:
    cleaned: list[str] = []
    for char in value:
        if char in "\r\n\u2028\u2029" or ord(char) < 32 or char == "\u007f":
            cleaned.append(" ")
        elif char == "\\":
            cleaned.append("\\\\")
        elif char == "|":
            cleaned.append("\\|")
        else:
            cleaned.append(char)
    return "".join(cleaned)
