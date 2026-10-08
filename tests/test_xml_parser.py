from decimal import Decimal
from pathlib import Path

from fapiao.parsers.xml_parser import parse_xml

DATA = Path(__file__).resolve().parents[1] / "samples" / "data"
BUYER = "91330000MA0000002Y"
SELLER = "91330000MA0000001X"


def test_english_xml_matches_sample_readme():
    invoice = parse_xml(DATA / "en" / "invoice.xml", "en/invoice.xml")
    assert invoice.number == "24330000000000000001"
    assert invoice.issue_date == "2026-10-01"
    assert invoice.kind == "专用"
    assert invoice.buyer_tax_id == BUYER
    assert invoice.seller_tax_id == SELLER
    assert invoice.amount == Decimal("100.00")
    assert invoice.tax_amount == Decimal("13.00")
    assert invoice.total == Decimal("113.00")
    assert invoice.issuer == "张三"
    assert invoice.verify_status == "未验签"
    assert len(invoice.lines) == 1
    line = invoice.lines[0]
    assert line.name == "办公用品"
    assert line.spec == "A4"
    assert line.unit == "箱"
    assert line.quantity == Decimal("2")
    assert line.unit_price == Decimal("50.00")
    assert line.amount == Decimal("100.00")
    assert line.tax_rate == Decimal("0.13")
    assert line.tax_amount == Decimal("13.00")
    assert line.tax_code == "1090511030000000000"
    assert line.tax_code_status == "正常"


def test_pinyin_xml_same_shape():
    invoice = parse_xml(DATA / "pinyin" / "invoice.xml", "pinyin/invoice.xml")
    assert invoice.number == "24330000000000000002"
    assert invoice.issue_date == "2026-10-02"
    assert invoice.kind == "普通"
    assert invoice.buyer_name == "示例购买方"
    assert invoice.buyer_tax_id == BUYER
    assert invoice.seller_tax_id == SELLER
    assert invoice.amount == Decimal("200.00")
    assert invoice.tax_amount == Decimal("6.00")
    assert invoice.total == Decimal("206.00")
    assert invoice.lines[0].name == "咨询服务"
    assert invoice.lines[0].tax_rate == Decimal("0.03")
    assert invoice.lines[0].tax_code_status == "正常"


def test_dump_prints_local_names():
    from fapiao.parsers.xml_parser import dump_tree

    text = dump_tree(DATA / "en" / "invoice.xml")
    assert "EIid" in text
    assert "TotalTax-includedAmount" in text
