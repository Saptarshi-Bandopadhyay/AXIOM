"""Local disk implementation of StorageInterface."""

import asyncio
from pathlib import Path
from app.config import get_settings
from app.interfaces.storage import StorageInterface


class LocalStorageService(StorageInterface):
    """Stores files on local disk."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self.base_dir = Path(base_dir or get_settings().UPLOAD_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, rel: str) -> Path:
        return self.base_dir / rel.lstrip("/")

    async def save(self, destination: str, content: bytes) -> str:
        target = self._path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, content)
        return destination

    async def load(self, source: str) -> bytes:
        return await asyncio.to_thread(self._path(source).read_bytes)

    async def delete(self, target: str) -> bool:
        path = self._path(target)
        if path.is_file():
            await asyncio.to_thread(path.unlink)
            return True
        return False

    def get_path(self, target: str) -> str:
        return str(self._path(target))
