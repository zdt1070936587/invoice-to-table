"""用发行侧私钥生成授权文件。私钥留在 dev_keys，不进仓库。"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fapiao.ed25519 import sign
from fapiao.license import PRODUCT_NAME, canonical_payload

SEED = Path(__file__).resolve().parents[1] / "dev_keys" / "ed25519.seed"


def main() -> None:
    parser = argparse.ArgumentParser(description="签发发票成表本地授权")
    parser.add_argument("--licensee", required=True)
    parser.add_argument("--expiry", required=True, help="YYYY-MM-DD")
    parser.add_argument("--seats", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    secret = SEED.read_bytes()
    payload = canonical_payload(PRODUCT_NAME, args.licensee, args.expiry, args.seats)
    document = {
        "product": PRODUCT_NAME,
        "licensee": args.licensee,
        "expiry": args.expiry,
        "seats": args.seats,
        "signature": base64.b64encode(sign(payload, secret)).decode("ascii"),
    }
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
