"""Klassenregeln. Dieselbe Tabelle steht in docs/klassen.md."""

from __future__ import annotations

import re

# Bei Gleichstand gewinnt die frühere Gruppe.
ORDER = ("mahnung", "auftrag", "angebot", "rechnung")

# Stichwort einmal zählen, Wortgrenze, längere Formen stehen extra.
KEYWORDS: dict[str, tuple[str, ...]] = {
    "mahnung": ("mahnung", "zahlungserinnerung", "payment reminder"),
    "auftrag": ("auftragsbestätigung", "auftrag", "bestellung", "purchase order"),
    "angebot": ("angebot", "quotation", "quote", "kostenvoranschlag"),
    "rechnung": ("rechnung", "invoice"),
}

THRESHOLD = 3
MARGIN = 2

_SCAN = 50_000
_CURRENCY = re.compile(r"€|\bEUR\b", re.IGNORECASE)
_AMOUNT_TOKEN = re.compile(
    r"(?<![\d.,])("
    r"-?\d{1,3}(?:,\d{3})+\.\d{2}"
    r"|-?\d{1,4}(?:[.\u00a0\u202f ]\d{3})+,\d{2}"
    r"|-?\d+,\d{2}"
    r"|-?\d+\.\d{2}"
    r")(?![\d.,])"
)
_NUMBER = re.compile(r"\b(?:RE-\d{4}-\d+|AN-\d+|PO-\d+|INV-\d+)\b", re.IGNORECASE)


def hits(text: str, keywords: tuple[str, ...]) -> int:
    """Stichwort einmal, am Wortanfang oder Wortende. Schlussrechnung zählt als Rechnung."""
    lowered = text.lower()
    count = 0
    for keyword in keywords:
        escaped = re.escape(keyword)
        if re.search(rf"(?<!\w){escaped}|{escaped}(?!\w)", lowered):
            count += 1
    return count


def decide(subject: str, body: str) -> tuple[str, str]:
    """Klasse und Sicherheit. Unter 3 Punkten immer sonstiges, niedrig."""
    scores = {
        name: 3 * hits(subject, KEYWORDS[name]) + hits(body, KEYWORDS[name])
        for name in ORDER
    }
    ranked = sorted(ORDER, key=lambda name: (-scores[name], ORDER.index(name)))
    best = ranked[0]
    best_score = scores[best]
    second = max(scores[name] for name in ORDER if name != best)
    if best_score < THRESHOLD:
        return "sonstiges", "niedrig"
    if best_score - second >= MARGIN:
        return best, "hoch"
    return best, "niedrig"


def rechnungsnummer(text: str) -> str | None:
    match = _NUMBER.search(text)
    if not match:
        return None
    return match.group(0).upper()


def betrag(text: str) -> str | None:
    sample = text[:_SCAN]
    for mark in _CURRENCY.finditer(sample):
        start = max(0, mark.start() - 40)
        window = sample[start : min(len(sample), mark.end() + 40)]
        currency_at = mark.start() - start
        currency_end = mark.end() - start
        best: re.Match[str] | None = None
        best_dist = 9
        for token in _AMOUNT_TOKEN.finditer(window):
            if token.end() <= currency_at:
                dist = currency_at - token.end()
            elif token.start() >= currency_end:
                dist = token.start() - currency_end
            else:
                dist = 0
            if dist < best_dist:
                best = token
                best_dist = dist
        if best is not None:
            return _normalize_amount(best.group(1))
    return None


def waehrung(text: str) -> str | None:
    if _CURRENCY.search(text[:_SCAN]):
        return "EUR"
    return None


def _normalize_amount(raw: str) -> str:
    negative = raw.startswith("-")
    raw = raw.lstrip("-")
    raw = raw.replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if "," in raw and raw.rfind(",") > raw.rfind("."):
        whole = raw.replace(".", "").replace(",", ".")
    else:
        whole = raw.replace(",", "")
    value = float(whole)
    if negative:
        value = -value
    return f"{value:.2f}"
