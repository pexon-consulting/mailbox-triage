"""Regeln, Report-Dateien und die fünf synthetischen Mails."""

from __future__ import annotations

import email
import json
import mailbox
from pathlib import Path

from mailbox_triage.classify import betrag, decide, waehrung
from mailbox_triage.cli import main
from mailbox_triage.parse import Zeile, load_path
from mailbox_triage.report import render_markdown

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
    assert "mailbox-triage@v0.1.0" in canonical
    assert "classify <pfad>" in canonical
    assert "null" in canonical
    assert "Rechnungskontrolle" in canonical


def test_betraege_komposita_und_kein_euro_in_europa() -> None:
    assert betrag("EUR 12,500.00") == "12500.00"
    assert betrag("€1,190.00") == "1190.00"
    assert betrag("1\u202f190,00 EUR") == "1190.00"
    assert betrag("1000.000,00 EUR") == "1000000.00"
    assert betrag("-1.190,00 EUR") == "-1190.00"
    assert betrag("EUR -480,00") == "-480.00"
    assert betrag("50,00 europäische Kunden") is None
    assert waehrung("Treffen in Europa") is None
    assert decide("Schlussrechnung RE-2026-0142", "") == ("rechnung", "hoch")


def test_charset_html_und_from_zeile(tmp_path: Path) -> None:
    kaputt = tmp_path / "kaputt.eml"
    kaputt.write_bytes(
        b"From: a@nordwerk.example\r\n"
        b"Subject: =?not-a-charset?b?UmVjaG51bmc=?=\r\n"
        b"Content-Type: text/plain; charset=unknown-8bit\r\n"
        b"\r\n"
        b"Rechnung RE-2026-0142 ueber 10,00 EUR\r\n"
    )
    assert load_path(kaputt)[0].klasse == "rechnung"
    assert main(["classify", str(kaputt), "--out", str(tmp_path / "report.md")]) == 0

    html = tmp_path / "html.eml"
    html.write_text(
        "From: a@nordwerk.example\n"
        "Subject: Unterlagen\n"
        "MIME-Version: 1.0\n"
        "Content-Type: multipart/alternative; boundary=grenze\n"
        "\n"
        "--grenze\n"
        "Content-Type: text/html; charset=utf-8\n"
        "\n"
        "<p>anbei die Rechnung ueber 1.190,00 EUR</p>\n"
        "--grenze--\n",
        encoding="utf-8",
    )
    assert load_path(html)[0].betrag == "1190.00"

    box = tmp_path / "mueller.mbox"
    box.write_bytes(
        "From Müller Fri Mar 13 12:00:00 2026\n"
        "From: a@nordwerk.example\n"
        "Subject: Rechnung RE-2026-0001\n"
        "\n"
        "Betrag 10,00 EUR\n".encode()
    )
    assert load_path(box)[0].klasse == "rechnung"


def test_markdown_bricht_keine_zeile() -> None:
    row = Zeile(
        datei="x.eml",
        klasse="sonstiges",
        sicherheit="niedrig",
        absender=None,
        betreff="Hallo\r\n# eingeschleust",
        datum=None,
        rechnungsnummer=None,
        betrag=None,
        waehrung=None,
        anhaenge=(),
    )
    markdown = render_markdown([row])
    assert "\r" not in markdown
    data = [line for line in markdown.splitlines() if line.startswith("| x.eml")]
    assert len(data) == 1
    assert "# eingeschleust" in data[0]
