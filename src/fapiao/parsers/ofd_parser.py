"""从 OFD 中取出内嵌发票 XML，再走同一套解析。"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fapiao.models import Invoice, ParseFailure
from fapiao.parsers.xml_parser import parse_xml
from fapiao.reasons import MESSAGES, OFD_NO_XML
from fapiao.sniff import FileKind, sniff
from fapiao.unpack import UnpackError, unpack_zip


def parse_ofd(path: Path, display_name: str) -> Invoice | ParseFailure:
    with tempfile.TemporaryDirectory(prefix="fapiao-ofd-") as temporary:
        dest = Path(temporary)
        try:
            members = unpack_zip(path, dest)
        except UnpackError:
            return ParseFailure(OFD_NO_XML, MESSAGES[OFD_NO_XML], display_name, parse_level="ofd-xml")
        embedded = [member for member in members if _contains_einvoice(member)]
        if not embedded:
            return ParseFailure(OFD_NO_XML, MESSAGES[OFD_NO_XML], display_name, parse_level="ofd-xml")
        chosen = _prefer_einvoice_root(embedded)
        parsed = parse_xml(chosen, display_name, parse_level="ofd-xml")
        if isinstance(parsed, Invoice):
            parsed.parse_level = "ofd-xml"
            parsed.source_files = [display_name]
        elif isinstance(parsed, ParseFailure):
            parsed.parse_level = "ofd-xml"
        return parsed


def _contains_einvoice(path: Path) -> bool:
    if sniff(path) not in (FileKind.XML, FileKind.UNKNOWN):
        return False
    try:
        blob = path.read_bytes()
    except OSError:
        return False
    return b"EInvoice" in blob or b"EInvoiceData" in blob


def _prefer_einvoice_root(paths: list[Path]) -> Path:
    for path in paths:
        head = path.read_bytes()[:4000]
        if b"<EInvoice" in head or b":EInvoice" in head:
            return path
    return paths[0]
