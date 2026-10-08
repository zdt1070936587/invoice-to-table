from pathlib import Path

import pytest

from fapiao.sniff import FileKind, sniff
from fapiao.unpack import UnpackError, unpack_zip

DATA = Path(__file__).resolve().parents[1] / "samples" / "data"


def test_sample_kinds():
    assert sniff(DATA / "en" / "invoice.xml") is FileKind.XML
    assert sniff(DATA / "ofd" / "invoice.ofd") is FileKind.OFD
    assert sniff(DATA / "mixed" / "bundle.zip") is FileKind.ZIP
    assert sniff(DATA / "pdf" / "invoice.pdf") is FileKind.PDF
    assert sniff(DATA / "photo" / "scan.jpg") is FileKind.IMAGE


def test_mixed_zip_lists_inner_types(tmp_path: Path):
    members = unpack_zip(DATA / "mixed" / "bundle.zip", tmp_path / "out")
    kinds = {path.name: sniff(path) for path in members}
    assert kinds["en_invoice.xml"] is FileKind.XML
    assert kinds["invoice.ofd"] is FileKind.OFD
    assert kinds["invoice.pdf"] is FileKind.PDF
    assert kinds["scan.jpg"] is FileKind.IMAGE


def test_path_escape_does_not_write_outside(tmp_path: Path):
    dest = tmp_path / "dest"
    with pytest.raises(UnpackError):
        unpack_zip(DATA / "malicious" / "traversal.zip", dest)
    assert not (tmp_path / "outside.txt").exists()
    assert not (dest / "outside.txt").exists()


def test_member_size_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import fapiao.unpack as unpack_mod

    monkeypatch.setattr(unpack_mod, "MAX_MEMBER_BYTES", 8)
    archive_path = tmp_path / "big.zip"
    import zipfile

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("note.txt", "0123456789")
    with pytest.raises(UnpackError, match="20MB|超过"):
        unpack_zip(archive_path, tmp_path / "out")
