"""Local filesystem implementation of StorageInterface."""

import asyncio
from pathlib import Path
from app.config import get_settings
from app.interfaces.storage import StorageInterface


class LocalStorageService(StorageInterface):
    """Stores and retrieves files on local disk under a configured root directory."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self.base_dir = Path(base_dir or get_settings().UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the base storage directory."""
        return self.base_dir / relative_path.lstrip("/")

    async def save(self, destination: str, content: bytes) -> str:
        """Save file bytes to disk and return the relative path."""
        target_path = self._resolve_path(destination)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target_path.write_bytes, content)
        return destination

    async def load(self, source: str) -> bytes:
        """Read and return file bytes from disk."""
        target_path = self._resolve_path(source)
        return await asyncio.to_thread(target_path.read_bytes)

    async def delete(self, target: str) -> bool:
        """Delete a file from disk if it exists."""
        target_path = self._resolve_path(target)
        if target_path.is_file():
            await asyncio.to_thread(target_path.unlink)
            return True
        return False

    def get_path(self, target: str) -> str:
        """Return the absolute filesystem path as a string."""
        return str(self._resolve_path(target))
