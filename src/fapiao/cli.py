"""命令行入口。无参数时打开窗口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fapiao.parsers.xml_parser import dump_tree
from fapiao.pipeline import run


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        from fapiao.ui import main as ui_main

        return ui_main()
    parser = argparse.ArgumentParser(prog="fapiao", description="发票成表 — 数电票整理成 Excel")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="整理文件夹或压缩包")
    run_parser.add_argument("path")
    run_parser.add_argument("--tax-id", required=True)
    run_parser.add_argument("--direction", required=True, choices=("in", "out"))
    run_parser.add_argument("--out")
    dump_parser = sub.add_parser("dump", help="打印 XML 标签树")
    dump_parser.add_argument("path")
    args = parser.parse_args(argv)
    if args.command == "dump":
        print(dump_tree(Path(args.path)))
        return 0
    if not args.tax_id.strip():
        print("税号不能为空", file=sys.stderr)
        return 2
    try:
        result = run(args.path, args.tax_id, args.direction, args.out)
    except (ValueError, FileNotFoundError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"合格 {result.qualified_count} 张，异常 {result.exception_count} 张")
    print(result.output_path)
    return 0
