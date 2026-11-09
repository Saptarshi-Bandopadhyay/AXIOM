"""Storage interface definition."""

from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract contract for document persistence."""

    @abstractmethod
    async def save(self, destination: str, content: bytes) -> str:
        """Save bytes to destination path, returning storage path."""
        pass

    @abstractmethod
    async def load(self, source: str) -> bytes:
        """Read bytes from storage path."""
        pass

    @abstractmethod
    async def delete(self, target: str) -> bool:
        """Delete file at target path. Returns True if deleted."""
        pass

    @abstractmethod
    def get_path(self, target: str) -> str:
        """Get absolute path or URI for target."""
        pass
