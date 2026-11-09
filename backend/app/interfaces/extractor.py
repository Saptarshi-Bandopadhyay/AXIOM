"""Document extraction interface and structured document data model."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class ExtractedDocument(BaseModel):
    """Normalized structured document model for an academic research paper."""

    title: str | None = None
    abstract: str | None = None
    methodology: str = ""
    experiments: str | None = None
    results: str | None = None
    full_text: str = ""
    sections: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractorInterface(ABC):
    """Abstract contract for document text and section extraction."""

    @abstractmethod
    async def extract_from_bytes(
        self, content: bytes, filename: str | None = None
    ) -> ExtractedDocument:
        """Extract text and segment sections from in-memory document bytes."""
        pass

    @abstractmethod
    async def extract_from_path(self, file_path: str) -> ExtractedDocument:
        """Extract text and segment sections from a local file path."""
        pass
