# Mailbox Triage

Mailbox Triage ist ein lokaler Postfach-Check. Er sortiert einen Export in Rechnung, Mahnung, Angebot und Auftrag. Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham.

```bash
npx skills add pexon-consulting/mailbox-triage
```

```bash
uvx --from git+https://github.com/pexon-consulting/mailbox-triage mailbox-triage classify ./postfach --out report.md
```

Claude Code hält das Skill aktuell mit `claude plugin marketplace add pexon-consulting/mailbox-triage`. Codex mit `codex plugin marketplace add pexon-consulting/mailbox-triage`. Die Zeile `npx skills add` ist die Kopie für beide. Sie zieht spätere Änderungen nicht von selbst.

## Klassen

Ein Stichwort im Betreff zählt 3 Punkte, ein Stichwort im Text zählt 1 Punkt. Ab 3 Punkten gilt die Klasse. Liegt der Vorsprung unter 2 Punkten, ist die Sicherheit niedrig. Unter 3 Punkten: `sonstiges`. Die volle Tabelle steht in [docs/klassen.md](docs/klassen.md).

| Klasse | Stichworte |
| --- | --- |
| mahnung | mahnung, zahlungserinnerung, payment reminder |
| auftrag | auftragsbestätigung, auftrag, bestellung, purchase order |
| angebot | angebot, quotation, quote, kostenvoranschlag |
| rechnung | rechnung, invoice |
| sonstiges | keines der Stichworte erreicht 3 Punkte |

Felder je Zeile: Datei, Klasse, Sicherheit, Absender, Betreff, Datum, Rechnungsnummer, Betrag, Währung, Anhänge. Ein Feld bleibt leer, wenn es nicht im Text steht. PDF-Anhänge werden nur mit Dateinamen genannt.

## Befehle

`mailbox-triage classify <pfad> --out report.md` liest eine `.eml`, eine `.mbox` oder einen Ordner und schreibt `report.md` plus `report.json`.

`mailbox-triage schema` schreibt die Regeln auf die Standardausgabe und legt keine Datei an.

Der Pfad bleibt lokal. Es gibt keinen IMAP-Abruf, keinen Upload und keinen Schreibweg nach SAP, DATEV oder ABAS.

## Für Agenten

Claude und Codex lesen [skills/mailbox-triage/SKILL.md](skills/mailbox-triage/SKILL.md). Dieselbe Datei liegt unter `.claude/skills/` und `.agents/skills/`. Nach einer Änderung an der kanonischen Datei: `python3 scripts/sync_skills.py`.

Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham. Nutzung nach MIT, ohne Support. Für den Einsatz bei Ihnen: https://pexon-consulting.de/ki-beratung/document-intelligence/
