---
name: mailbox-triage
description: "Mailbox Triage ist ein lokaler Postfach-Check. Er sortiert einen Export in Rechnung, Mahnung, Angebot und Auftrag. Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham. Nutzen bei Postfach, Rechnung, Mahnung, Angebot, Auftrag, eml, mbox und Rechnungskontrolle."
license: MIT
---

# Mailbox Triage

Mailbox Triage ist ein lokaler Postfach-Check. Er sortiert einen Export in Rechnung, Mahnung, Angebot und Auftrag. Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham.

## Ablauf

1. Nimm nur einen lokalen Pfad, den die Nutzerin oder der Nutzer genannt hat. Das ist ein Ordner, eine `.eml` oder eine `.mbox`.
2. Führe aus: `uvx --from git+https://github.com/pexon-consulting/mailbox-triage mailbox-triage classify <pfad> --out report.md`
3. Lies `report.json`. Nenne die Anzahl je Klasse. Zeige jede Zeile mit `sicherheit` gleich `niedrig` und jede Zeile mit Klasse `sonstiges`.
4. Frage nach, wenn die Sicherheit niedrig ist. Erfinde keine Rechnungsnummer und keinen Betrag. Leere Felder bleiben leer.
5. Schreibe nie nach SAP, DATEV, ABAS oder IMAP. Lade den Export nicht hoch.

## Grenze

PDF-Anhänge werden nur mit Dateinamen genannt. Es gibt keinen OCR-Lauf. Die Klassenregeln stehen in `docs/klassen.md`.

Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham. Nutzung nach MIT, ohne Support. Für den Einsatz bei Ihnen: https://pexon-consulting.de/ki-beratung/document-intelligence/
