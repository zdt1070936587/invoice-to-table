"""候选标签解析数电票 XML。缺字段时用 dump 补标签，不复制解析函数。"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from lxml import etree

from fapiao.models import Invoice, LineItem, ParseFailure, money
from fapiao.reasons import UNKNOWN_SCHEMA, UNSUPPORTED_KIND, MESSAGES

NUMBER_TAGS = ("EIid", "InvoiceNumber", "Fphm")
DATE_TAGS = ("RequestTime", "IssueTime", "IssueDate", "Kprq")
BUYER_NAME_TAGS = ("BuyerName", "Gmfmc")
BUYER_TAX_TAGS = ("BuyerIdNum", "Gmfnsrsbh")
SELLER_NAME_TAGS = ("SellerName", "Xsfmc")
SELLER_TAX_TAGS = ("SellerIdNum", "Xsfnsrsbh")
AMOUNT_TAGS = ("TotalAmWithoutTax", "Hjje")
TAX_TAGS = ("TotalTaxAm", "Hjse")
TOTAL_TAGS = ("TotalTax-includedAmount", "Jshj")
ISSUER_TAGS = ("Drawer", "Kpr")
KIND_TAGS = ("LabelName", "Fppz", "InvoiceType")
RED_FLAG_TAGS = ("Sflzfp", "RedInvoice", "IsRed")

LINE_NAME_TAGS = ("ItemName", "Spmc")
LINE_SPEC_TAGS = ("SpecMod", "Ggxh")
LINE_UNIT_TAGS = ("MeaUnits", "Dw")
LINE_QTY_TAGS = ("Quantity", "Sl")
LINE_PRICE_TAGS = ("UnPrice", "Dj")
LINE_AMOUNT_TAGS = ("Amount", "Je")
LINE_RATE_TAGS = ("TaxRate", "Slv")
LINE_TAX_TAGS = ("ComTaxAm", "Se")
LINE_CODE_TAGS = ("TaxClassificationCode", "Spbm")

_UNSUPPORTED = ("铁路电子客票", "航空运输电子客票", "财政票据", "非税收入")
_RED_YES = {"Y", "YES", "TRUE", "1", "是"}
_DATE_CN = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
_DATE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
_DATE_COMPACT = re.compile(r"(\d{4})(\d{2})(\d{2})")


def dump_tree(path: Path) -> str:
    root = etree.parse(str(path)).getroot()
    lines: list[str] = []

    def walk(element: etree._Element, depth: int) -> None:
        qname = etree.QName(element)
        namespace = qname.namespace or ""
        lines.append(f"{'  ' * depth}{qname.localname}  [{namespace}]")
        for child in element:
            walk(child, depth + 1)

    walk(root, 0)
    return "\n".join(lines)


def parse_xml(path: Path, display_name: str, parse_level: str = "xml") -> Invoice | ParseFailure:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="ignore")
    for keyword in _UNSUPPORTED:
        if keyword in text:
            return ParseFailure(
                UNSUPPORTED_KIND,
                MESSAGES[UNSUPPORTED_KIND],
                display_name,
                parse_level=parse_level,
            )
    try:
        root = etree.fromstring(raw)
    except etree.XMLSyntaxError:
        return _schema_failure(display_name, parse_level)

    number = _first_text(root, NUMBER_TAGS)
    if not re.fullmatch(r"\d{20}", number):
        return _schema_failure(display_name, parse_level, number)
    try:
        amount = _money_text(root, AMOUNT_TAGS)
        tax_amount = _money_text(root, TAX_TAGS)
        total = _money_text(root, TOTAL_TAGS)
        issue_date = parse_date(_first_text(root, DATE_TAGS))
    except (InvalidOperation, ValueError):
        return _schema_failure(display_name, parse_level, number)

    red_marked = _red_marked(root)
    lines = [_parse_line(element) for element in _line_elements(root)]
    return Invoice(
        number=number,
        issue_date=issue_date,
        kind=_kind(root),
        is_red=red_marked or total < 0,
        buyer_name=_first_text(root, BUYER_NAME_TAGS),
        buyer_tax_id=_first_text(root, BUYER_TAX_TAGS),
        seller_name=_first_text(root, SELLER_NAME_TAGS),
        seller_tax_id=_first_text(root, SELLER_TAX_TAGS),
        amount=amount,
        tax_amount=tax_amount,
        total=total,
        issuer=_first_text(root, ISSUER_TAGS),
        source_files=[display_name],
        parse_level=parse_level,
        lines=lines,
        red_marked=red_marked,
    )


def parse_date(text: str) -> str:
    matched = _DATE_CN.search(text)
    if matched:
        year, month, day = (int(part) for part in matched.groups())
        return datetime(year, month, day).strftime("%Y-%m-%d")
    matched = _DATE_ISO.search(text)
    if matched:
        return f"{matched.group(1)}-{matched.group(2)}-{matched.group(3)}"
    matched = _DATE_COMPACT.search(text)
    if matched:
        year, month, day = (int(part) for part in matched.groups())
        return datetime(year, month, day).strftime("%Y-%m-%d")
    raise ValueError(f"无法识别开票日期：{text}")


def parse_rate(text: str) -> tuple[Decimal, str]:
    raw = text.strip()
    if raw in ("免税", "不征税"):
        return Decimal("0"), raw
    if raw.endswith("%"):
        rate = (Decimal(raw[:-1].strip()) / Decimal("100")).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP,
        )
        return rate, raw
    return Decimal(raw), raw


def _schema_failure(filename: str, parse_level: str, number: str = "") -> ParseFailure:
    return ParseFailure(
        UNKNOWN_SCHEMA,
        MESSAGES[UNKNOWN_SCHEMA],
        filename,
        number=number,
        parse_level=parse_level,
    )


def _local(element: etree._Element) -> str:
    return etree.QName(element).localname


def _first_text(root: etree._Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for element in root.iter():
        if _local(element) in wanted:
            text = "".join(element.itertext()).strip()
            if text:
                return text
    return ""


def _money_text(root: etree._Element, names: tuple[str, ...]) -> Decimal:
    text = _first_text(root, names)
    if not text:
        raise ValueError("缺少金额")
    cleaned = text.replace(",", "").replace("，", "").replace("¥", "").replace("￥", "").strip()
    return money(cleaned)


def _kind(root: etree._Element) -> str:
    blob = " ".join(_tagged_texts(root, KIND_TAGS))
    if "专用" in blob:
        return "专用"
    return "普通"


def _red_marked(root: etree._Element) -> bool:
    for text in _tagged_texts(root, KIND_TAGS):
        if "红字" in text:
            return True
    for text in _tagged_texts(root, RED_FLAG_TAGS):
        if text.strip().upper() in _RED_YES:
            return True
    return False


def _tagged_texts(root: etree._Element, names: tuple[str, ...]) -> list[str]:
    wanted = set(names)
    found: list[str] = []
    for element in root.iter():
        if _local(element) in wanted:
            text = "".join(element.itertext()).strip()
            if text:
                found.append(text)
    return found


def _line_elements(root: etree._Element) -> list[etree._Element]:
    name_tags = set(LINE_NAME_TAGS)
    found: list[etree._Element] = []
    for element in root.iter():
        for child in element:
            if _local(child) in name_tags and (child.text or "").strip():
                found.append(element)
                break
    return [element for element in found if not any(_is_ancestor(element, other) for other in found)]


def _is_ancestor(ancestor: etree._Element, node: etree._Element) -> bool:
    parent = node.getparent()
    while parent is not None:
        if parent is ancestor:
            return True
        parent = parent.getparent()
    return False


def _parse_line(element: etree._Element) -> LineItem:
    rate_text = _child_text(element, LINE_RATE_TAGS)
    rate, rate_label = parse_rate(rate_text) if rate_text else (Decimal("0"), "")
    code = _child_text(element, LINE_CODE_TAGS)
    return LineItem(
        name=_child_text(element, LINE_NAME_TAGS),
        spec=_child_text(element, LINE_SPEC_TAGS),
        unit=_child_text(element, LINE_UNIT_TAGS),
        quantity=_optional_decimal(_child_text(element, LINE_QTY_TAGS)),
        unit_price=_optional_decimal(_child_text(element, LINE_PRICE_TAGS)),
        amount=money(_child_text(element, LINE_AMOUNT_TAGS) or "0"),
        tax_rate=rate,
        tax_rate_text=rate_label,
        tax_amount=money(_child_text(element, LINE_TAX_TAGS) or "0"),
        tax_code=code,
        tax_code_status="正常" if re.fullmatch(r"\d{19}", code) else "编码缺失",
    )


def _child_text(element: etree._Element, names: tuple[str, ...]) -> str:
    wanted = set(names)
    for child in element:
        if _local(child) in wanted and (child.text or "").strip():
            return (child.text or "").strip()
    return ""


def _optional_decimal(text: str) -> Decimal | None:
    if not text:
        return None
    cleaned = text.replace(",", "").replace("，", "").strip()
    return Decimal(cleaned)
