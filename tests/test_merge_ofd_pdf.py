from decimal import Decimal
from pathlib import Path

from fapiao.merge import merge
from fapiao.models import Invoice, money
from fapiao.parsers.ofd_parser import parse_ofd
from fapiao.parsers.pdf_parser import parse_pdf
from fapiao.parsers.xml_parser import parse_xml
from fapiao.reasons import DUP_CONFLICT, OFD_NO_XML, PDF_ONLY

DATA = Path(__file__).resolve().parents[1] / "samples" / "data"


def test_ofd_matches_xml_number_and_total():
    xml_invoice = parse_xml(DATA / "ofd" / "invoice.xml", "invoice.xml")
    ofd_invoice = parse_ofd(DATA / "ofd" / "invoice.ofd", "invoice.ofd")
    assert ofd_invoice.number == xml_invoice.number == "24330000000000000003"
    assert ofd_invoice.total == xml_invoice.total == Decimal("339.00")
    assert ofd_invoice.parse_level == "ofd-xml"


def test_ofd_without_xml():
    failure = parse_ofd(DATA / "ofd" / "no_xml.ofd", "no_xml.ofd")
    assert failure.code == OFD_NO_XML


def test_pdf_extracts_number_and_total():
    parsed = parse_pdf(DATA / "pdf" / "invoice.pdf", "invoice.pdf")
    assert parsed.number == "24330000000000000001"
    assert parsed.pdf_total == Decimal("113.00")


def test_xml_plus_pdf_keeps_xml_amount():
    xml_invoice = parse_xml(DATA / "en" / "invoice.xml", "en.xml")
    pdf_invoice = parse_pdf(DATA / "pdf" / "invoice.pdf", "en.pdf")
    pdf_invoice.pdf_total = money("1.00")
    pdf_invoice.total = money("1.00")
    merged, exceptions = merge([xml_invoice, pdf_invoice], [])
    assert len(merged) == 1
    assert merged[0].invoice.total == Decimal("113.00")
    assert merged[0].invoice.source_files == ["en.xml", "en.pdf"]
    assert exceptions == []


def test_pdf_only_stays_out_of_summary():
    pdf_invoice = parse_pdf(DATA / "pdf" / "invoice.pdf", "only.pdf")
    merged, exceptions = merge([pdf_invoice], [])
    assert merged == []
    assert exceptions[0].code == PDF_ONLY


def test_conflict_and_photo():
    from fapiao.sniff import FileKind, sniff

    left = parse_xml(DATA / "en" / "invoice.xml", "a.xml")
    right = parse_xml(DATA / "en" / "invoice.xml", "b.xml")
    right.total = money("1.00")
    merged, exceptions = merge([left, right], [])
    assert merged == []
    assert {row.code for row in exceptions} == {DUP_CONFLICT}
    assert sniff(DATA / "photo" / "scan.jpg") is FileKind.IMAGE
