"""发票与明细。金额一律为 Decimal。"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


def money(value: Decimal | str | int) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def norm_tax_id(value: str) -> str:
    return "".join(value.split()).upper()


@dataclass
class LineItem:
    name: str
    spec: str
    unit: str
    quantity: Decimal | None
    unit_price: Decimal | None
    amount: Decimal
    tax_rate: Decimal
    tax_rate_text: str
    tax_amount: Decimal
    tax_code: str
    tax_code_status: str


@dataclass
class Invoice:
    number: str
    issue_date: str
    kind: str
    is_red: bool
    buyer_name: str
    buyer_tax_id: str
    seller_name: str
    seller_tax_id: str
    amount: Decimal
    tax_amount: Decimal
    total: Decimal
    issuer: str
    source_files: list[str]
    parse_level: str
    lines: list[LineItem] = field(default_factory=list)
    verify_status: str = "未验签"
    red_marked: bool = False
    pdf_total: Decimal | None = None


@dataclass
class ParseFailure:
    code: str
    message: str
    filename: str
    number: str = ""
    parse_level: str = ""


@dataclass
class ExceptionRow:
    filename: str
    number: str
    code: str
    message: str
    parse_level: str


@dataclass
class RunResult:
    qualified_count: int
    exception_count: int
    output_path: Path
    invoices: list[Invoice]
    exceptions: list[ExceptionRow]
