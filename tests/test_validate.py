from decimal import Decimal

from fapiao.models import Invoice, LineItem, money
from fapiao.reasons import AMOUNT_MISMATCH, OK, RED_INVOICE, TAX_ID_MISMATCH, TAX_MISMATCH
from fapiao.validate import validate

BUYER = "91330000MA0000002Y"


def _line(amount: str, rate: str, tax: str, rate_text: str | None = None) -> LineItem:
    return LineItem(
        name="项目",
        spec="",
        unit="",
        quantity=Decimal("1"),
        unit_price=money(amount),
        amount=money(amount),
        tax_rate=Decimal(rate),
        tax_rate_text=rate_text if rate_text is not None else rate,
        tax_amount=money(tax),
        tax_code="1" * 19,
        tax_code_status="正常",
    )


def _invoice(lines: list[LineItem], amount: str, tax: str, total: str, buyer: str = BUYER) -> Invoice:
    return Invoice(
        number="24330000000000000099",
        issue_date="2026-10-08",
        kind="专用",
        is_red=money(total) < 0,
        buyer_name="购买方",
        buyer_tax_id=buyer,
        seller_name="销售方",
        seller_tax_id="91330000MA0000001X",
        amount=money(amount),
        tax_amount=money(tax),
        total=money(total),
        issuer="",
        source_files=["fake"],
        parse_level="xml",
        lines=lines,
    )


def test_real_sample_passes():
    from pathlib import Path

    from fapiao.parsers.xml_parser import parse_xml

    invoice = parse_xml(Path("samples/data/en/invoice.xml"), "en/invoice.xml")
    verdict = validate(invoice, BUYER, "in")
    assert verdict.code == OK
    assert verdict.in_summary


def test_amount_short_by_one_yuan():
    invoice = _invoice([_line("99.00", "0.13", "12.87")], "100.00", "12.87", "112.87")
    verdict = validate(invoice, BUYER, "in")
    assert verdict.code == AMOUNT_MISMATCH
    assert not verdict.in_summary


def test_tax_rate_wrong():
    invoice = _invoice([_line("100.00", "0.13", "1.00")], "100.00", "1.00", "101.00")
    verdict = validate(invoice, BUYER, "in")
    assert verdict.code == TAX_MISMATCH


def test_buyer_tax_id_wrong():
    invoice = _invoice([_line("100.00", "0.13", "13.00")], "100.00", "13.00", "113.00", buyer="91330000MA0000099Z")
    verdict = validate(invoice, "91 330000ma0000002y", "in")
    assert verdict.code == TAX_ID_MISMATCH


def test_red_sample_keeps_negative_sign():
    from pathlib import Path

    from fapiao.parsers.xml_parser import parse_xml

    invoice = parse_xml(Path("samples/data/red/invoice.xml"), "red/invoice.xml")
    verdict = validate(invoice, BUYER, "in")
    assert verdict.code == RED_INVOICE
    assert invoice.total == Decimal("-113.00")
    assert verdict.in_summary
