"""打印 XML 标签树。也可以用 python -m fapiao dump。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fapiao.parsers.xml_parser import dump_tree


def main() -> None:
    if len(sys.argv) != 2:
        print("用法: python scripts/dump_tags.py 某文件.xml", file=sys.stderr)
        raise SystemExit(2)
    print(dump_tree(Path(sys.argv[1])))


if __name__ == "__main__":
    main()
