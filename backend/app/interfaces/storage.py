"""Storage interface defining the contract for file persistence.

Decouples file operations from concrete storage implementations (local disk, S3, GCS).
"""

from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract contract for document and file storage."""

    @abstractmethod
    async def save(self, destination: str, content: bytes) -> str:
        """Save file bytes to the destination path. Returns the saved path."""
        pass

    @abstractmethod
    async def load(self, source: str) -> bytes:
        """Load and return file bytes from the source path."""
        pass

    @abstractmethod
    async def delete(self, target: str) -> bool:
        """Delete file at the target path. Returns True if deleted, False otherwise."""
        pass

    @abstractmethod
    def get_path(self, target: str) -> str:
        """Return the resolved filesystem path or URI for the target."""
        pass
