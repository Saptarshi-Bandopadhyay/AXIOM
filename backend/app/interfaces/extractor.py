"""Abstract document extractor interface defining contracts for PDF parsing.

Decouples document parsing and section segmentation logic from concrete libraries
(e.g., PyMuPDF, OCR engines, Marker) per ADR-002.
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class ExtractedDocument(BaseModel):
    """Normalized structured representation of an extracted academic research paper."""

    title: str | None = Field(
        default=None,
        description="Detected paper title.",
    )
    abstract: str | None = Field(
        default=None,
        description="Extracted abstract section text.",
    )
    methodology: str | None = Field(
        default=None,
        description="Extracted methodology or approach section text.",
    )
    experiments: str | None = Field(
        default=None,
        description="Extracted experimental setup and configuration text.",
    )
    results: str | None = Field(
        default=None,
        description="Extracted results and evaluation metrics text.",
    )
    full_text: str = Field(
        default="",
        description="Full text extracted from the document in reading order.",
    )
    sections: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping identified section headers to their extracted text.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extraction diagnostics, page count, and document metadata.",
    )


class ExtractorInterface(ABC):
    """Abstract base class defining the contract for document extraction providers."""

    @abstractmethod
    async def extract_from_bytes(
        self, content: bytes, filename: str | None = None
    ) -> ExtractedDocument:
        """Extract text and segment sections directly from in-memory document bytes.

        Args:
            content: Raw binary document bytes (e.g., PDF content).
            filename: Optional original filename for logging or format heuristics.

        Returns:
            ExtractedDocument: Structured document model containing extracted sections.

        Raises:
            ValueError: If document bytes are corrupted or in an unsupported format.
            IOError: If extraction engine encounters a processing failure.
        """
        pass

    @abstractmethod
    async def extract_from_path(self, file_path: str) -> ExtractedDocument:
        """Extract text and segment sections from a document file path.

        Args:
            file_path: Local filesystem path to the target document.

        Returns:
            ExtractedDocument: Structured document model containing extracted sections.

        Raises:
            FileNotFoundError: If the target file does not exist.
            ValueError: If the file is corrupted or unsupported.
            IOError: If extraction fails.
        """
        pass
