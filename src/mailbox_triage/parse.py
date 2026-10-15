"""Liest .eml, .mbox und Ordner. Kein Netz, kein IMAP."""

from __future__ import annotations

import email
import re
from dataclasses import dataclass
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

from mailbox_triage.classify import betrag, decide, rechnungsnummer, waehrung

MAX_BYTES = 32 * 1024 * 1024
MAX_MESSAGES = 5000
_HTML = re.compile(r"(?is)<(script|style)\b.*?>.*?</\1>|<[^>]+>")


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
    raw = _read_limited(path)
    if suffix == ".mbox":
        chunks = _split_mbox(raw)
        if len(chunks) > MAX_MESSAGES:
            raise ValueError(f"Mehr als {MAX_MESSAGES} Nachrichten: {path.name}")
        return [
            parse_message(email.message_from_bytes(chunk), f"{path.name}#{index}")
            for index, chunk in enumerate(chunks, start=1)
        ]
    if suffix == ".eml":
        return [parse_message(email.message_from_bytes(raw), path.name)]
    raise ValueError(f"Nur .eml, .mbox oder ein Ordner: {path}")


def _read_limited(path: Path) -> bytes:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"Datei größer als 32 MB: {path.name}")
    return path.read_bytes()


def _split_mbox(raw: bytes) -> list[bytes]:
    messages: list[list[bytes]] = []
    current: list[bytes] = []
    saw_from = False
    for line in raw.splitlines(keepends=True):
        if line.startswith(b"From "):
            saw_from = True
            if current:
                messages.append(current)
            current = []
            continue
        current.append(line)
    if current:
        messages.append(current)
    if not saw_from:
        return [raw] if raw.strip() else []
    return [b"".join(item) for item in messages if b"".join(item).strip()]


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
            parts.append(_decode_bytes(value, charset))
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
        text = _decode_part(message)
        if message.get_content_type() == "text/html":
            return _strip_html(text), []
        return text, []
    texts: list[str] = []
    htmls: list[str] = []
    files: list[str] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disposition = part.get_content_disposition()
        if ctype == "text/plain" and disposition != "attachment":
            texts.append(_decode_part(part))
            continue
        if ctype == "text/html" and disposition != "attachment":
            htmls.append(_decode_part(part))
            continue
        filename = part.get_filename()
        if filename:
            files.append(_header_value(filename))
    if any(item.strip() for item in texts):
        return "\n".join(texts), files
    if htmls:
        return "\n".join(_strip_html(item) for item in htmls), files
    return "", files


def _header_value(value: str) -> str:
    parts: list[str] = []
    for chunk, charset in decode_header(value):
        if isinstance(chunk, bytes):
            parts.append(_decode_bytes(chunk, charset))
        else:
            parts.append(chunk)
    return "".join(parts)


def _decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""
    if not isinstance(payload, bytes):
        return ""
    return _decode_bytes(payload, part.get_content_charset())


def _decode_bytes(payload: bytes, charset: str | None) -> str:
    try:
        return payload.decode(charset or "utf-8", errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    return re.sub(r"\s+", " ", _HTML.sub(" ", html)).strip()
