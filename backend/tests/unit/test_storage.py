"""Unit tests for LocalStorageService file persistence."""

from pathlib import Path
from app.services.local_storage import LocalStorageService


async def test_storage_lifecycle_save_load_delete(tmp_path: Path) -> None:
    """Verify saving, reading, resolving, and deleting files on local disk."""
    storage = LocalStorageService(base_dir=tmp_path)
    relative_path = "papers/test_paper.pdf"
    content = b"%PDF-1.4 sample content"

    # Save file and verify relative return path
    saved_path = await storage.save(relative_path, content)
    assert saved_path == relative_path

    # Verify physical file existence via get_path
    physical_path = Path(storage.get_path(relative_path))
    assert physical_path.is_file()

    # Read content back
    loaded_content = await storage.load(relative_path)
    assert loaded_content == content

    # Delete file and verify removal
    assert await storage.delete(relative_path) is True
    assert await storage.delete(relative_path) is False
    assert not physical_path.exists()
