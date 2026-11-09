"""Local filesystem storage implementation of StorageInterface.

Manages saving, loading, existence checks, and deletion of research paper PDF files
on the local filesystem with path traversal protection and non-blocking asynchronous I/O.
"""

import asyncio
from pathlib import Path
from app.config import get_settings
from app.interfaces.storage import StorageInterface


class LocalStorageService(StorageInterface):
    """Local filesystem storage provider implementing StorageInterface."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        """Initialize storage service with a target base directory.

        Args:
            base_dir: Root directory for stored files. Defaults to settings.UPLOAD_DIR.
        """
        if base_dir is None:
            settings = get_settings()
            self.base_dir = settings.UPLOAD_DIR.resolve()
        else:
            self.base_dir = Path(base_dir).resolve()

        # Ensure root storage directory exists on disk
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve target path and prevent directory traversal security attacks.

        Args:
            relative_path: Path or filename relative to base_dir.

        Returns:
            Path: Verified absolute target path within base_dir.

        Raises:
            ValueError: If target path escapes base_dir.
        """
        # Strip leading slashes to prevent absolute path escapes
        clean_rel = relative_path.lstrip("/\\")
        target = (self.base_dir / clean_rel).resolve()

        # Guard against directory traversal attacks (e.g., ../../etc/passwd)
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(f"Path traversal attempt detected: {relative_path}")

        return target

    async def save(self, destination_path: str, content: bytes) -> str:
        """Persist binary file content to disk asynchronously.

        Args:
            destination_path: Relative destination path within storage root.
            content: Raw binary bytes to persist.

        Returns:
            str: Normalized relative path identifier of the saved file.
        """
        target = self._resolve_safe_path(destination_path)

        def _sync_write() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        # Offload synchronous disk write to thread pool to avoid blocking asyncio event loop
        await asyncio.to_thread(_sync_write)
        return str(target.relative_to(self.base_dir))

    async def load(self, source_path: str) -> bytes:
        """Retrieve binary file content from disk asynchronously.

        Args:
            source_path: Relative storage path of target file.

        Returns:
            bytes: Binary content read from disk.

        Raises:
            FileNotFoundError: If the target file does not exist.
        """
        target = self._resolve_safe_path(source_path)

        if not await asyncio.to_thread(target.is_file):
            raise FileNotFoundError(f"File not found in storage: {source_path}")

        return await asyncio.to_thread(target.read_bytes)

    async def exists(self, target_path: str) -> bool:
        """Check whether a file exists at the relative path.

        Args:
            target_path: Relative storage path.

        Returns:
            bool: True if path points to an existing file, False otherwise.
        """
        try:
            target = self._resolve_safe_path(target_path)
            return await asyncio.to_thread(target.is_file)
        except ValueError:
            # Traversal attempts do not exist in valid storage
            return False

    async def delete(self, target_path: str) -> bool:
        """Remove a file from disk if present.

        Args:
            target_path: Relative storage path.

        Returns:
            bool: True if the file was deleted, False if not found.
        """
        target = self._resolve_safe_path(target_path)

        def _sync_delete() -> bool:
            if target.is_file():
                target.unlink()
                return True
            return False

        return await asyncio.to_thread(_sync_delete)

    def get_path(self, target_path: str) -> str:
        """Return the resolved absolute filesystem path.

        Args:
            target_path: Relative storage path.

        Returns:
            str: Absolute path string on disk.
        """
        return str(self._resolve_safe_path(target_path))
