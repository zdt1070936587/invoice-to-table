"""读取程序目录里的本地授权。只校验签名和到期日。"""

from __future__ import annotations

import base64
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fapiao.ed25519 import verify

PRODUCT_NAME = "发票成表"
PUBLIC_KEY = bytes.fromhex("d0eb0664e5c7817364b4425c9d6c38e8d07af353bf02628ff01165b6c8600b95")
FREE_INVOICE_LIMIT = 5


@dataclass(frozen=True)
class LicenseStatus:
    active: bool
    expiry: str
    licensee: str
    seats: int

    @property
    def label(self) -> str:
        if self.active:
            return f"授权至 {self.expiry}"
        return "免费"


def license_path(directory: Path | None = None) -> Path:
    if directory is not None:
        return directory / "license.json"
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "license.json"
    return Path.cwd() / "license.json"


def canonical_payload(product: str, licensee: str, expiry: str, seats: int) -> bytes:
    body = {
        "expiry": expiry,
        "licensee": licensee,
        "product": product,
        "seats": seats,
    }
    return json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def load_license(
    directory: Path | None = None,
    public_key: bytes | None = None,
    today: date | None = None,
) -> LicenseStatus:
    inactive = LicenseStatus(False, "", "", 0)
    path = license_path(directory)
    if not path.is_file():
        return inactive
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        product = str(data["product"])
        licensee = str(data["licensee"])
        expiry = str(data["expiry"])
        seats = int(data["seats"])
        signature = base64.b64decode(str(data["signature"]), validate=True)
        expiry_day = date.fromisoformat(expiry)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return inactive
    if product != PRODUCT_NAME or seats < 1:
        return inactive
    key = public_key if public_key is not None else PUBLIC_KEY
    payload = canonical_payload(product, licensee, expiry, seats)
    if not verify(payload, signature, key):
        return inactive
    current = today or date.today()
    if expiry_day < current:
        return LicenseStatus(False, expiry, licensee, seats)
    return LicenseStatus(True, expiry, licensee, seats)


def summary_limit(
    directory: Path | None = None,
    public_key: bytes | None = None,
    today: date | None = None,
) -> int | None:
    status = load_license(directory, public_key, today)
    if status.active:
        return None
    return FREE_INVOICE_LIMIT
