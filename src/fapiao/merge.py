"""按 20 位发票号码合并。有 XML 时金额以 XML 为准。"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from fapiao.models import ExceptionRow, Invoice, ParseFailure, norm_tax_id
from fapiao.reasons import DUP_CONFLICT, DUP_INVOICE, MESSAGES, PDF_ONLY

_AUTHORITATIVE = {"xml", "ofd-xml"}


@dataclass
class MergedInvoice:
    invoice: Invoice
    duplicates: list[Invoice]


def merge(
    invoices: list[Invoice],
    failures: list[ParseFailure],
) -> tuple[list[MergedInvoice], list[ExceptionRow]]:
    exceptions = [
        ExceptionRow(item.filename, item.number, item.code, item.message, item.parse_level)
        for item in failures
    ]
    groups: OrderedDict[str, list[Invoice]] = OrderedDict()
    for invoice in invoices:
        groups.setdefault(invoice.number, []).append(invoice)

    merged: list[MergedInvoice] = []
    for number, group in groups.items():
        authoritative = [item for item in group if item.parse_level in _AUTHORITATIVE]
        pdfs = [item for item in group if item.parse_level == "pdf-only"]
        if not authoritative:
            for pdf in pdfs:
                exceptions.append(
                    ExceptionRow(pdf.source_files[0], number, PDF_ONLY, MESSAGES[PDF_ONLY], "pdf-only")
                )
            continue
        if len({_signature(item) for item in authoritative}) > 1:
            for item in authoritative:
                exceptions.append(
                    ExceptionRow(
                        item.source_files[0],
                        number,
                        DUP_CONFLICT,
                        MESSAGES[DUP_CONFLICT],
                        item.parse_level,
                    )
                )
            for pdf in pdfs:
                exceptions.append(
                    ExceptionRow(pdf.source_files[0], number, PDF_ONLY, MESSAGES[PDF_ONLY], "pdf-only")
                )
            continue
        kept = authoritative[0]
        sources: list[str] = []
        for item in authoritative:
            _append_unique(sources, item.source_files)
        for pdf in pdfs:
            _append_unique(sources, pdf.source_files)
        kept.source_files = sources
        merged.append(MergedInvoice(kept, authoritative[1:]))
    return merged, exceptions


def duplicate_rows(item: MergedInvoice) -> list[ExceptionRow]:
    return [
        ExceptionRow(
            extra.source_files[0],
            item.invoice.number,
            DUP_INVOICE,
            MESSAGES[DUP_INVOICE],
            extra.parse_level,
        )
        for extra in item.duplicates
    ]


def _signature(invoice: Invoice) -> tuple[object, ...]:
    lines = tuple((line.amount, line.tax_amount) for line in invoice.lines)
    return (
        invoice.number,
        invoice.issue_date,
        norm_tax_id(invoice.buyer_tax_id),
        norm_tax_id(invoice.seller_tax_id),
        invoice.amount,
        invoice.tax_amount,
        invoice.total,
        lines,
    )


def _append_unique(target: list[str], names: list[str]) -> None:
    for name in names:
        if name not in target:
            target.append(name)
