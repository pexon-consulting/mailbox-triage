# Klassen eines FiBu-Postfachs

Mailbox Triage ist ein lokaler Postfach-Check. Er sortiert einen Export in Rechnung, Mahnung, Angebot und Auftrag. Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham.

## Entscheidungsregel

Der Befehl liest Betreff und Text. Ein Stichwort im Betreff zählt 3 Punkte, ein Stichwort im Text zählt 1 Punkt. Jedes Stichwort zählt einmal, am Wortanfang oder am Wortende. Schlussrechnung und Rechnungsnummer zählen deshalb als Rechnung. Ab 3 Punkten gilt die Klasse. Liegt der Vorsprung vor der nächsten Klasse unter 2 Punkten, ist die Sicherheit niedrig. Unter 3 Punkten ist die Klasse `sonstiges` und die Sicherheit niedrig. Bei Gleichstand gewinnt die frühere Zeile dieser Tabelle.

PDF-Anhänge werden nur mit Dateinamen genannt. Der Befehl schreibt nicht nach IMAP, SAP, DATEV oder ABAS.

| Klasse | Stichworte | Felder, leer wenn nicht im Text |
| --- | --- | --- |
| mahnung | mahnung, zahlungserinnerung, payment reminder | Absender, Betreff, Datum, Rechnungsnummer, Betrag, Währung, Anhänge |
| auftrag | auftragsbestätigung, auftrag, bestellung, purchase order | Absender, Betreff, Datum, Rechnungsnummer, Betrag, Währung, Anhänge |
| angebot | angebot, quotation, quote, kostenvoranschlag | Absender, Betreff, Datum, Rechnungsnummer, Betrag, Währung, Anhänge |
| rechnung | rechnung, invoice | Absender, Betreff, Datum, Rechnungsnummer, Betrag, Währung, Anhänge |
| sonstiges | keines der Stichworte erreicht 3 Punkte | dieselben Felder, Sicherheit immer niedrig |

Rechnungsnummern, die der Befehl erkennt: `RE-2026-0142`, `AN-88`, `PO-4401`, `INV-100`. Beträge stehen neben `EUR` oder `€`, zum Beispiel `1.190,00 EUR`. Die Währung ist `EUR`, wenn `EUR` oder `€` im Text steht.

Beispiel von Pexon Consulting GmbH, gepflegt von Phillip Pham. Nutzung nach MIT, ohne Support. Für den Einsatz bei Ihnen: https://pexon-consulting.de/ki-beratung/document-intelligence/
