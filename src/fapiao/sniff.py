"""按文件头判断格式，不信扩展名。"""

from __future__ import annotations

import zipfile
from enum import Enum
from pathlib import Path


class FileKind(Enum):
    XML = "xml"
    OFD = "ofd"
    ZIP = "zip"
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


def sniff(path: Path) -> FileKind:
    with path.open("rb") as handle:
        header = handle.read(64)
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        if _zip_root_has_ofd(path):
            return FileKind.OFD
        return FileKind.ZIP
    if header.startswith(b"%PDF"):
        return FileKind.PDF
    if _is_image(header):
        return FileKind.IMAGE
    if _is_xml(header):
        return FileKind.XML
    return FileKind.UNKNOWN


def _is_xml(header: bytes) -> bool:
    stripped = header.lstrip(b"\xef\xbb\xbf \t\r\n")
    return stripped.startswith((b"<?xml", b"<"))


def _is_image(header: bytes) -> bool:
    if header.startswith(b"\xff\xd8\xff"):
        return True
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if header.startswith((b"GIF87a", b"GIF89a")):
        return True
    if header.startswith(b"BM"):
        return True
    if header.startswith((b"II*\x00", b"MM\x00*")):
        return True
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return True
    return False


def _zip_root_has_ofd(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                normalized = name.replace("\\", "/").lstrip("/")
                if normalized.lower() == "ofd.xml":
                    return True
    except zipfile.BadZipFile:
        return False
    return False
