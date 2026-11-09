"""Abstract storage interface defining the contract for file persistence.

Decouples file storage operations from specific storage providers (e.g., local disk,
Amazon S3, Google Cloud Storage) per ADR-009.
"""

from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Abstract base class defining the contract for file storage providers."""

    @abstractmethod
    async def save(self, destination_path: str, content: bytes) -> str:
        """Persist binary file content to the target destination path or key.

        Args:
            destination_path: Relative destination path or object key.
            content: Raw binary file bytes to write.

        Returns:
            str: Resolved storage identifier or local path of the saved file.

        Raises:
            IOError: If writing to the storage provider fails.
        """
        pass

    @abstractmethod
    async def load(self, source_path: str) -> bytes:
        """Retrieve binary file content from storage.

        Args:
            source_path: Relative storage path or object key.

        Returns:
            bytes: Raw binary content of the file.

        Raises:
            FileNotFoundError: If the requested file does not exist.
            IOError: If reading from the storage provider fails.
        """
        pass

    @abstractmethod
    async def exists(self, target_path: str) -> bool:
        """Check whether a file exists at the given path or key.

        Args:
            target_path: Relative storage path or object key to test.

        Returns:
            bool: True if file exists, False otherwise.
        """
        pass

    @abstractmethod
    async def delete(self, target_path: str) -> bool:
        """Remove a file from storage if it exists.

        Args:
            target_path: Relative storage path or object key to remove.

        Returns:
            bool: True if the file was deleted, False if it was not found.

        Raises:
            IOError: If deletion fails due to permission or I/O errors.
        """
        pass

    @abstractmethod
    def get_path(self, target_path: str) -> str:
        """Resolve a storage path or key to a canonical URI or absolute path.

        Args:
            target_path: Relative storage path or object key.

        Returns:
            str: Resolved path string or URI representation.
        """
        pass
