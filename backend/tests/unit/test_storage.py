"""Tests for LocalStorageService."""

from pathlib import Path
from app.services.local_storage import LocalStorageService


async def test_storage_lifecycle(tmp_path: Path) -> None:
    storage = LocalStorageService(base_dir=tmp_path)
    file_rel = "papers/test.pdf"
    content = b"%PDF-1.4 dummy"

    assert await storage.save(file_rel, content) == file_rel
    assert await storage.load(file_rel) == content
    assert Path(storage.get_path(file_rel)).is_file()
    assert await storage.delete(file_rel) is True
    assert await storage.delete(file_rel) is False
