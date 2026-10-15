"""Liest .eml, .mbox und Ordner. Kein Netz, kein IMAP."""

from __future__ import annotations

import email
import mailbox
from dataclasses import dataclass
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

from mailbox_triage.classify import betrag, decide, rechnungsnummer, waehrung


@dataclass(frozen=True)
class Zeile:
    datei: str
    klasse: str
    sicherheit: str
    absender: str | None
    betreff: str | None
    datum: str | None
    rechnungsnummer: str | None
    betrag: str | None
    waehrung: str | None
    anhaenge: tuple[str, ...]


def load_path(path: Path) -> list[Zeile]:
    if path.is_dir():
        files = [
            item
            for item in sorted(path.rglob("*"))
            if item.is_file()
            and item.suffix.lower() in {".eml", ".mbox"}
            and not any(part.startswith(".") for part in item.relative_to(path).parts)
        ]
        rows: list[Zeile] = []
        for item in files:
            rows.extend(load_file(item))
        return rows
    return load_file(path)


def load_file(path: Path) -> list[Zeile]:
    suffix = path.suffix.lower()
    if suffix == ".mbox":
        box = mailbox.mbox(path)
        try:
            return [
                parse_message(message, f"{path.name}#{index}")
                for index, message in enumerate(box, start=1)
            ]
        finally:
            box.close()
    if suffix == ".eml":
        message = email.message_from_bytes(path.read_bytes())
        return [parse_message(message, path.name)]
    raise ValueError(f"Nur .eml, .mbox oder ein Ordner: {path}")


def parse_message(message: Message, datei: str) -> Zeile:
    subject = _header(message, "Subject")
    body, attachments = _body_and_attachments(message)
    klasse, sicherheit = decide(subject, body)
    text = f"{subject}\n{body}"
    return Zeile(
        datei=datei,
        klasse=klasse,
        sicherheit=sicherheit,
        absender=_absender(message),
        betreff=subject or None,
        datum=_datum(message),
        rechnungsnummer=rechnungsnummer(text),
        betrag=betrag(text),
        waehrung=waehrung(text),
        anhaenge=tuple(attachments),
    )


def _header(message: Message, name: str) -> str:
    raw = message.get(name)
    if raw is None:
        return ""
    parts: list[str] = []
    for value, charset in decode_header(raw):
        if isinstance(value, bytes):
            parts.append(value.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(value)
    return "".join(parts).strip()


def _absender(message: Message) -> str | None:
    name, address = parseaddr(_header(message, "From"))
    if name and address:
        return f"{name} <{address}>"
    return address or name or None


def _datum(message: Message) -> str | None:
    raw = _header(message, "Date")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _body_and_attachments(message: Message) -> tuple[str, list[str]]:
    if not message.is_multipart():
        return _decode_part(message), []
    texts: list[str] = []
    files: list[str] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        filename = part.get_filename()
        if filename:
            files.append(_header_value(filename))
            continue
        if part.get_content_disposition() == "attachment":
            continue
        if part.get_content_type() == "text/plain":
            texts.append(_decode_part(part))
    return "\n".join(texts), files


def _header_value(value: str) -> str:
    parts: list[str] = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts)


def _decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")
