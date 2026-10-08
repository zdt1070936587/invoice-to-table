"""只从 PDF 文字层读取 20 位发票号码和价税合计。"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from fapiao.models import Invoice, ParseFailure, money
from fapiao.reasons import MESSAGES, NEEDS_OCR, PDF_NUMBER_MISSING, PDF_ONLY, UNSUPPORTED_KIND

_UNSUPPORTED = ("铁路电子客票", "航空运输电子客票", "财政票据", "非税收入")
_NUMBER_LABELED = re.compile(r"(?:发票号码|发票号|InvoiceNumber|EIid)\D{0,30}(\d{20})")
_NUMBER_BARE = re.compile(r"(?<!\d)(\d{20})(?!\d)")
_TOTAL_LABELED = re.compile(r"(?:价税合计|（小写）|\(小写\))\D{0,40}(\d+\.\d{2})")


def parse_pdf(path: Path, display_name: str) -> Invoice | ParseFailure:
    try:
        reader = PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except (PdfReadError, OSError, ValueError):
        return ParseFailure(NEEDS_OCR, MESSAGES[NEEDS_OCR], display_name, parse_level="pdf-only")
    if any(keyword in text for keyword in _UNSUPPORTED):
        return ParseFailure(
            UNSUPPORTED_KIND,
            MESSAGES[UNSUPPORTED_KIND],
            display_name,
            parse_level="pdf-only",
        )
    if not text.strip():
        return ParseFailure(NEEDS_OCR, MESSAGES[NEEDS_OCR], display_name, parse_level="pdf-only")
    number = _invoice_number(text)
    total = _total(text)
    if not number:
        return ParseFailure(
            PDF_ONLY,
            PDF_NUMBER_MISSING,
            display_name,
            parse_level="pdf-only",
        )
    return Invoice(
        number=number,
        issue_date="",
        kind="",
        is_red=False,
        buyer_name="",
        buyer_tax_id="",
        seller_name="",
        seller_tax_id="",
        amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total=total if total is not None else Decimal("0.00"),
        issuer="",
        source_files=[display_name],
        parse_level="pdf-only",
        pdf_total=total,
    )


def _invoice_number(text: str) -> str:
    labeled = _NUMBER_LABELED.search(text)
    if labeled:
        return labeled.group(1)
    found = _NUMBER_BARE.findall(text)
    if len(found) == 1:
        return found[0]
    return ""


def _total(text: str) -> Decimal | None:
    matched = _TOTAL_LABELED.search(text.replace(",", "").replace("，", ""))
    if not matched:
        return None
    try:
        return money(matched.group(1))
    except (InvalidOperation, ValueError):
        return None
