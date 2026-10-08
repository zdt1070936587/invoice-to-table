"""解开压缩包。限制大小，并拒绝写到目标目录外面。"""

from __future__ import annotations

import zipfile
from pathlib import Path

MAX_ZIP_BYTES = 200 * 1024 * 1024
MAX_MEMBER_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 200 * 1024 * 1024
MAX_DEPTH = 5
MAX_MEMBERS = 2000


class UnpackError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def unpack_zip(src: Path, dest: Path) -> list[Path]:
    size = src.stat().st_size
    if size > MAX_ZIP_BYTES:
        raise UnpackError("压缩包超过 200MB")
    dest.mkdir(parents=True, exist_ok=True)
    dest_root = dest.resolve()
    extracted: list[Path] = []
    total = 0
    count = 0
    try:
        archive = zipfile.ZipFile(src)
    except zipfile.BadZipFile as exc:
        raise UnpackError("压缩包无法打开") from exc
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            count += 1
            if count > MAX_MEMBERS:
                raise UnpackError("压缩包内文件数量超过 2000")
            if info.file_size > MAX_MEMBER_BYTES:
                raise UnpackError(f"内部文件超过 20MB：{info.filename}")
            total += info.file_size
            if total > MAX_TOTAL_BYTES:
                raise UnpackError("解压总大小超过 200MB")
            _reject_unsafe_name(info.filename)
            target = (dest / info.filename).resolve()
            if not target.is_relative_to(dest_root):
                raise UnpackError(f"压缩包路径逃逸：{info.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            written = 0
            with archive.open(info, "r") as source, target.open("wb") as sink:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_MEMBER_BYTES:
                        sink.close()
                        target.unlink(missing_ok=True)
                        raise UnpackError(f"内部文件超过 20MB：{info.filename}")
                    sink.write(chunk)
            extracted.append(target)
    return extracted


def _reject_unsafe_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    if normalized.startswith("/") or (len(normalized) >= 2 and normalized[1] == ":"):
        raise UnpackError(f"压缩包路径不安全：{name}")
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        raise UnpackError(f"压缩包路径逃逸：{name}")
