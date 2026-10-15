"""Regeln, Report-Dateien und die fünf synthetischen Mails."""

from __future__ import annotations

import email
import json
import mailbox
from pathlib import Path

from mailbox_triage.classify import decide
from mailbox_triage.cli import main
from mailbox_triage.parse import load_path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def test_fuenf_fixtures_klassen() -> None:
    rows = {row.datei: row for row in load_path(FIXTURES)}
    rechnung = rows["rechnung.eml"]
    assert rechnung.klasse == "rechnung"
    assert rechnung.sicherheit == "hoch"
    assert rechnung.rechnungsnummer == "RE-2026-0142"
    assert rechnung.betrag == "1190.00"
    assert rechnung.waehrung == "EUR"
    assert rechnung.datum == "2026-03-02"
    assert rechnung.absender == "Nordwerk GmbH <buchhaltung@nordwerk.example>"
    assert rechnung.anhaenge == ("rechnung.pdf",)

    mahnung = rows["mahnung.eml"]
    assert mahnung.klasse == "mahnung"
    assert mahnung.sicherheit == "hoch"
    assert mahnung.betrag == "480.00"

    assert rows["angebot.eml"].klasse == "angebot"
    assert rows["angebot.eml"].rechnungsnummer == "AN-88"
    assert rows["auftrag.eml"].klasse == "auftrag"
    assert rows["auftrag.eml"].rechnungsnummer == "PO-4401"
    assert rows["sonstiges.eml"].klasse == "sonstiges"
    assert rows["sonstiges.eml"].sicherheit == "niedrig"
    assert rows["sonstiges.eml"].betrag is None
    assert rows["sonstiges.eml"].waehrung is None


def test_gleichstand_ist_niedrig_und_body_unter_schwelle() -> None:
    klasse, sicherheit = decide("Mahnung zur Rechnung", "")
    assert klasse == "mahnung"
    assert sicherheit == "niedrig"
    assert decide("Wochenplan", "Bitte die invoice prüfen") == ("sonstiges", "niedrig")


def test_classify_schreibt_nur_den_report(tmp_path: Path) -> None:
    quelle = tmp_path / "postfach"
    quelle.mkdir()
    original = (FIXTURES / "rechnung.eml").read_bytes()
    (quelle / "rechnung.eml").write_bytes(original)
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}

    out = tmp_path / "ausgabe" / "report.md"
    assert main(["classify", str(quelle), "--out", str(out)]) == 0

    after = {path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()}
    neu = after - {path for path in before if (tmp_path / path).is_file()}
    assert neu == {Path("ausgabe/report.md"), Path("ausgabe/report.json")}
    assert (quelle / "rechnung.eml").read_bytes() == original

    payload = json.loads((tmp_path / "ausgabe" / "report.json").read_text(encoding="utf-8"))
    assert payload["zeilen"][0]["klasse"] == "rechnung"
    assert "SAP" not in (tmp_path / "ausgabe" / "report.md").read_text(encoding="utf-8")


def test_schema_schreibt_keine_datei(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["schema"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schwelle"] == 3
    assert data["schreibt_nicht"] == ["imap", "sap", "datev", "abas"]
    assert list(tmp_path.iterdir()) == []


def test_mbox_und_fehlender_pfad(tmp_path: Path) -> None:
    box_path = tmp_path / "sammel.mbox"
    box = mailbox.mbox(box_path)
    message = email.message_from_bytes((FIXTURES / "angebot.eml").read_bytes())
    box.add(message)
    box.close()
    rows = load_path(box_path)
    assert rows[0].datei == "sammel.mbox#1"
    assert rows[0].klasse == "angebot"
    assert main(["classify", str(tmp_path / "fehlt.eml"), "--out", str(tmp_path / "report.md")]) == 2


def test_skill_kopien_sind_gleich() -> None:
    canonical = (ROOT / "skills" / "mailbox-triage" / "SKILL.md").read_text(encoding="utf-8")
    claude = (ROOT / ".claude" / "skills" / "mailbox-triage" / "SKILL.md").read_text(encoding="utf-8")
    codex = (ROOT / ".agents" / "skills" / "mailbox-triage" / "SKILL.md").read_text(encoding="utf-8")
    assert canonical == claude == codex
    assert "uvx --from git+https://github.com/pexon-consulting/mailbox-triage" in canonical
    assert "Rechnungskontrolle" in canonical
