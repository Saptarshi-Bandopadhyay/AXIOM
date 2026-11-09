"""Unit tests for StorageInterface abstract base class."""

import pytest
from app.interfaces.storage import StorageInterface


def test_cannot_instantiate_abstract_storage_interface() -> None:
    """Verify that StorageInterface cannot be directly instantiated."""
    with pytest.raises(TypeError) as exc_info:
        StorageInterface()  # type: ignore[abstract]

    assert "Can't instantiate abstract class StorageInterface" in str(exc_info.value)


def test_incomplete_subclass_cannot_be_instantiated() -> None:
    """Verify that a subclass omitting abstract methods cannot be instantiated."""

    class IncompleteStorage(StorageInterface):
        async def save(self, destination_path: str, content: bytes) -> str:
            return destination_path

    with pytest.raises(TypeError) as exc_info:
        IncompleteStorage()  # type: ignore[abstract]

    assert "Can't instantiate abstract class IncompleteStorage" in str(exc_info.value)


async def test_complete_subclass_instantiates_and_executes() -> None:
    """Verify that a subclass implementing all methods instantiates cleanly."""

    class InMemoryStorage(StorageInterface):
        def __init__(self) -> None:
            self._store: dict[str, bytes] = {}

        async def save(self, destination_path: str, content: bytes) -> str:
            self._store[destination_path] = content
            return destination_path

        async def load(self, source_path: str) -> bytes:
            if source_path not in self._store:
                raise FileNotFoundError(f"{source_path} not found")
            return self._store[source_path]

        async def exists(self, target_path: str) -> bool:
            return target_path in self._store

        async def delete(self, target_path: str) -> bool:
            if target_path in self._store:
                del self._store[target_path]
                return True
            return False

        def get_path(self, target_path: str) -> str:
            return f"memory://{target_path}"

    storage = InMemoryStorage()
    assert await storage.exists("test.pdf") is False

    saved_path = await storage.save("test.pdf", b"%PDF-1.4 dummy content")
    assert saved_path == "test.pdf"
    assert await storage.exists("test.pdf") is True

    loaded_content = await storage.load("test.pdf")
    assert loaded_content == b"%PDF-1.4 dummy content"

    assert storage.get_path("test.pdf") == "memory://test.pdf"

    deleted = await storage.delete("test.pdf")
    assert deleted is True
    assert await storage.exists("test.pdf") is False
