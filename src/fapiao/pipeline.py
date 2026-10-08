"""嗅探、解析、合并、校验、限额，然后写出 Excel。"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

from fapiao.export_xlsx import export_workbook
from fapiao.license import summary_limit
from fapiao.merge import duplicate_rows, merge
from fapiao.models import ExceptionRow, Invoice, ParseFailure, RunResult
from fapiao.parsers.ofd_parser import parse_ofd
from fapiao.parsers.pdf_parser import parse_pdf
from fapiao.parsers.xml_parser import parse_xml
from fapiao.reasons import LICENSE_LIMIT, MESSAGES, NEEDS_OCR, UNKNOWN_FILE, UNPACK_REJECTED
from fapiao.sniff import FileKind, sniff
from fapiao.unpack import MAX_DEPTH, UnpackError, unpack_zip
from fapiao.validate import validate


def default_output_name(direction: str, today: date | None = None) -> str:
    day = (today or date.today()).strftime("%Y%m%d")
    prefix = "进项" if direction == "in" else "销项"
    return f"{prefix}_{day}.xlsx"


def run(
    path: Path | str,
    tax_id: str,
    direction: str,
    out: Path | str | None = None,
    *,
    license_dir: Path | None = None,
    license_public_key: bytes | None = None,
    today: date | None = None,
) -> RunResult:
    if direction not in ("in", "out"):
        raise ValueError("direction 只能是 in 或 out")
    if not str(tax_id).strip():
        raise ValueError("税号不能为空")
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    output = Path(out) if out is not None else Path(default_output_name(direction, today))
    mtimes = _mtimes(source)

    with tempfile.TemporaryDirectory(prefix="fapiao-") as temporary:
        found, failures = _collect(source, Path(temporary))
        invoices: list[Invoice] = []
        for item_path, display_name, kind in found:
            parsed = _parse_one(item_path, display_name, kind)
            if isinstance(parsed, Invoice):
                invoices.append(parsed)
            else:
                failures.append(parsed)

    merged, exceptions = merge(invoices, failures)
    qualified_items = []
    for item in merged:
        verdict = validate(item.invoice, tax_id, direction)
        if verdict.in_summary:
            qualified_items.append(item)
            exceptions.extend(duplicate_rows(item))
        else:
            primary = item.invoice.source_files[0]
            exceptions.append(
                ExceptionRow(
                    primary,
                    item.invoice.number,
                    verdict.code,
                    verdict.message,
                    item.invoice.parse_level,
                )
            )

    qualified_items.sort(key=lambda item: (item.invoice.issue_date, item.invoice.number))
    limit = summary_limit(license_dir, license_public_key, today)
    if limit is not None and len(qualified_items) > limit:
        kept = qualified_items[:limit]
        for extra in qualified_items[limit:]:
            exceptions.append(
                ExceptionRow(
                    extra.invoice.source_files[0],
                    extra.invoice.number,
                    LICENSE_LIMIT,
                    MESSAGES[LICENSE_LIMIT],
                    extra.invoice.parse_level,
                )
            )
        qualified_items = kept

    for item in qualified_items:
        if item.invoice.is_red:
            exceptions.append(
                ExceptionRow(
                    item.invoice.source_files[0],
                    item.invoice.number,
                    "RED_INVOICE",
                    MESSAGES["RED_INVOICE"],
                    item.invoice.parse_level,
                )
            )

    exceptions.sort(key=lambda row: (row.code, row.filename, row.number))
    invoices_out = [item.invoice for item in qualified_items]
    export_workbook(output, invoices_out, exceptions)
    _assert_unchanged(mtimes)
    return RunResult(len(invoices_out), len(exceptions), output, invoices_out, exceptions)


def _parse_one(path: Path, display_name: str, kind: FileKind) -> Invoice | ParseFailure:
    if kind is FileKind.XML:
        return parse_xml(path, display_name)
    if kind is FileKind.OFD:
        return parse_ofd(path, display_name)
    if kind is FileKind.PDF:
        return parse_pdf(path, display_name)
    if kind is FileKind.IMAGE:
        return ParseFailure(NEEDS_OCR, MESSAGES[NEEDS_OCR], display_name, parse_level="")
    return ParseFailure(UNKNOWN_FILE, MESSAGES[UNKNOWN_FILE], display_name, parse_level="")


def _collect(source: Path, temporary: Path) -> tuple[list[tuple[Path, str, FileKind]], list[ParseFailure]]:
    found: list[tuple[Path, str, FileKind]] = []
    failures: list[ParseFailure] = []

    def handle_file(path: Path, display_name: str, depth: int) -> None:
        kind = sniff(path)
        if kind is FileKind.ZIP:
            if depth >= MAX_DEPTH:
                failures.append(
                    ParseFailure(UNPACK_REJECTED, "压缩包嵌套超过 5 层", display_name)
                )
                return
            dest = temporary / f"zip-{len(found)}-{depth}"
            try:
                members = unpack_zip(path, dest)
            except UnpackError as exc:
                failures.append(ParseFailure(UNPACK_REJECTED, exc.message, display_name))
                return
            for member in members:
                relative = member.relative_to(dest).as_posix()
                handle_file(member, f"{display_name}!/{relative}", depth + 1)
            return
        found.append((path, display_name, kind))

    if source.is_file():
        handle_file(source, source.name, 0)
        return found, failures
    for child in sorted(source.rglob("*")):
        if child.is_file():
            handle_file(child, child.relative_to(source).as_posix(), 0)
    return found, failures


def _mtimes(source: Path) -> dict[Path, int]:
    files = [source] if source.is_file() else [path for path in source.rglob("*") if path.is_file()]
    return {path: path.stat().st_mtime_ns for path in files}


def _assert_unchanged(before: dict[Path, int]) -> None:
    for path, stamp in before.items():
        if path.stat().st_mtime_ns != stamp:
            raise RuntimeError(f"原始文件被改动：{path}")
