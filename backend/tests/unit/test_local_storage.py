"""Unit tests for LocalStorageService."""

from pathlib import Path
import pytest
from app.services.local_storage import LocalStorageService


async def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """Verify writing and reading binary file content using LocalStorageService."""
    storage = LocalStorageService(base_dir=tmp_path)
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    relative_path = "papers/test_paper.pdf"
    saved_key = await storage.save(relative_path, content)
    assert saved_key == "papers/test_paper.pdf"

    loaded_content = await storage.load(relative_path)
    assert loaded_content == content


async def test_nested_directory_creation(tmp_path: Path) -> None:
    """Verify automatic creation of nested intermediate directories."""
    storage = LocalStorageService(base_dir=tmp_path)
    content = b"sample text"

    deep_path = "year/2026/month/11/day/09/data.bin"
    await storage.save(deep_path, content)

    full_disk_path = tmp_path / deep_path
    assert full_disk_path.is_file()
    assert full_disk_path.read_bytes() == content


async def test_exists_and_delete_behavior(tmp_path: Path) -> None:
    """Verify file existence checking and deletion."""
    storage = LocalStorageService(base_dir=tmp_path)
    file_key = "session_123/upload.pdf"

    assert await storage.exists(file_key) is False
    assert await storage.delete(file_key) is False

    await storage.save(file_key, b"binary_data")
    assert await storage.exists(file_key) is True

    deleted = await storage.delete(file_key)
    assert deleted is True
    assert await storage.exists(file_key) is False


async def test_load_non_existent_file_raises_error(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when attempting to load missing files."""
    storage = LocalStorageService(base_dir=tmp_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        await storage.load("missing_folder/missing_file.pdf")

    assert "File not found in storage" in str(exc_info.value)


async def test_path_traversal_prevention(tmp_path: Path) -> None:
    """Verify that path traversal attempts raise ValueError and are blocked."""
    storage = LocalStorageService(base_dir=tmp_path)

    with pytest.raises(ValueError) as exc_info:
        await storage.save("../../escape.txt", b"malicious content")
    assert "Path traversal attempt detected" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        await storage.load("../outside.txt")
    assert "Path traversal attempt detected" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        await storage.delete("../outside.txt")
    assert "Path traversal attempt detected" in str(exc_info.value)

    # exists should return False rather than crash
    assert await storage.exists("../outside.txt") is False


def test_get_path_returns_canonical_absolute_path(tmp_path: Path) -> None:
    """Verify get_path returns the absolute filesystem path."""
    storage = LocalStorageService(base_dir=tmp_path)
    resolved = storage.get_path("docs/file.pdf")
    expected = str((tmp_path / "docs/file.pdf").resolve())
    assert resolved == expected
