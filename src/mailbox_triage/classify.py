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

_AMOUNT = re.compile(
    r"(?:EUR|€)\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})"
    r"|(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d{1,3}(?:,\d{3})*\.\d{2}|\d+\.\d{2})\s*(?:EUR|€)",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b(?:RE-\d{4}-\d+|AN-\d+|PO-\d+|INV-\d+)\b", re.IGNORECASE)


def hits(text: str, keywords: tuple[str, ...]) -> int:
    lowered = text.lower()
    count = 0
    for keyword in keywords:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
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
    match = _AMOUNT.search(text)
    if not match:
        return None
    raw = next(group for group in match.groups() if group)
    return _normalize_amount(raw)


def waehrung(text: str) -> str | None:
    if re.search(r"EUR|€", text, re.IGNORECASE):
        return "EUR"
    return None


def _normalize_amount(raw: str) -> str:
    if "," in raw and raw.rfind(",") > raw.rfind("."):
        whole = raw.replace(".", "").replace(",", ".")
    else:
        whole = raw.replace(",", "")
    return f"{float(whole):.2f}"
