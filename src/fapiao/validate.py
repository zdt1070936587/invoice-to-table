"""用 Decimal 做勾稽和税号核对。允许相差 0.01 元。"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fapiao.models import Invoice, norm_tax_id
from fapiao.reasons import (
    AMOUNT_MISMATCH,
    MESSAGES,
    OK,
    RED_INVOICE,
    RED_SIGN_MISMATCH,
    TAX_ID_MISMATCH,
    TAX_MISMATCH,
)

TOLERANCE = Decimal("0.01")
_ZERO_RATE_LABELS = {"免税", "不征税"}


@dataclass(frozen=True)
class Verdict:
    code: str
    message: str
    in_summary: bool


def validate(invoice: Invoice, tax_id: str, direction: str) -> Verdict:
    if invoice.red_marked and invoice.total >= 0:
        return Verdict(AMOUNT_MISMATCH, RED_SIGN_MISMATCH, False)
    if not _close(sum((line.amount for line in invoice.lines), Decimal("0.00")), invoice.amount):
        return _fail(AMOUNT_MISMATCH)
    if not _close(sum((line.tax_amount for line in invoice.lines), Decimal("0.00")), invoice.tax_amount):
        return _fail(AMOUNT_MISMATCH)
    if not _close(invoice.amount + invoice.tax_amount, invoice.total):
        return _fail(AMOUNT_MISMATCH)
    for line in invoice.lines:
        if line.tax_rate_text in _ZERO_RATE_LABELS:
            if line.tax_amount != 0:
                return _fail(TAX_MISMATCH)
            continue
        if not _close(line.amount * line.tax_rate, line.tax_amount):
            return _fail(TAX_MISMATCH)
    expected = norm_tax_id(tax_id)
    actual = norm_tax_id(invoice.buyer_tax_id if direction == "in" else invoice.seller_tax_id)
    if actual != expected:
        return _fail(TAX_ID_MISMATCH)
    if invoice.is_red:
        return Verdict(RED_INVOICE, MESSAGES[RED_INVOICE], True)
    return Verdict(OK, MESSAGES[OK], True)


def _close(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) <= TOLERANCE


def _fail(code: str) -> Verdict:
    return Verdict(code, MESSAGES[code], False)
