# Mailbox Triage

Mailbox Triage ist ein lokaler Postfach-Check. Er sortiert einen Export in Rechnung, Mahnung, Angebot und Auftrag. Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham.

Ein Befehl:

```bash
uvx --from git+https://github.com/pexon-consulting/mailbox-triage mailbox-triage classify ./postfach --out report.md
```

Lies danach `report.json`. Zeige die Anzahl je Klasse und jede Zeile mit `sicherheit` gleich `niedrig`.

Ausgabe je Zeile: `datei`, `klasse`, `sicherheit` (`hoch` oder `niedrig`), `absender`, `betreff`, `datum`, `rechnungsnummer`, `betrag`, `waehrung`, `anhaenge`. Leere Felder sind `null`. Erfinde keine Werte.

Grenze: nur der genannte lokale Pfad. Kein IMAP, kein Upload, kein Schreiben nach SAP, DATEV oder ABAS. PDF-Anhänge nur als Dateiname. Kein OCR.

Die Klassenregeln stehen in `docs/klassen.md`. Die Skill-Datei wird nur in `skills/mailbox-triage/SKILL.md` geändert, danach `python3 scripts/sync_skills.py`.
