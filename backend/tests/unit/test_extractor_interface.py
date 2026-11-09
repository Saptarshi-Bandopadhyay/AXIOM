"""Unit tests for ExtractorInterface and ExtractedDocument."""

import pytest
from app.interfaces.extractor import ExtractedDocument, ExtractorInterface


def test_cannot_instantiate_abstract_extractor_interface() -> None:
    """Verify that ExtractorInterface cannot be directly instantiated."""
    with pytest.raises(TypeError) as exc_info:
        ExtractorInterface()  # type: ignore[abstract]

    assert "Can't instantiate abstract class ExtractorInterface" in str(exc_info.value)


def test_incomplete_extractor_subclass_cannot_be_instantiated() -> None:
    """Verify that an extractor subclass omitting abstract methods cannot be instantiated."""

    class IncompleteExtractor(ExtractorInterface):
        async def extract_from_bytes(
            self, content: bytes, filename: str | None = None
        ) -> ExtractedDocument:
            return ExtractedDocument(full_text="test")

    with pytest.raises(TypeError) as exc_info:
        IncompleteExtractor()  # type: ignore[abstract]

    assert "Can't instantiate abstract class IncompleteExtractor" in str(exc_info.value)


async def test_complete_extractor_subclass_instantiates_and_executes() -> None:
    """Verify that a complete extractor subclass executes correctly."""

    class MockExtractor(ExtractorInterface):
        async def extract_from_bytes(
            self, content: bytes, filename: str | None = None
        ) -> ExtractedDocument:
            return ExtractedDocument(
                title="Mock Paper",
                abstract="Mock Abstract",
                methodology="Mock Methodology",
                experiments="Mock Experiments",
                results="Mock Results",
                full_text=content.decode("utf-8", errors="replace"),
                sections={"Methodology": "Mock Methodology"},
                metadata={"page_count": 1, "filename": filename},
            )

        async def extract_from_path(self, file_path: str) -> ExtractedDocument:
            return await self.extract_from_bytes(b"content from file", filename=file_path)

    extractor = MockExtractor()

    doc_from_bytes = await extractor.extract_from_bytes(b"sample bytes", filename="paper.pdf")
    assert doc_from_bytes.title == "Mock Paper"
    assert doc_from_bytes.methodology == "Mock Methodology"
    assert doc_from_bytes.full_text == "sample bytes"
    assert doc_from_bytes.metadata["filename"] == "paper.pdf"

    doc_from_path = await extractor.extract_from_path("/tmp/paper.pdf")
    assert doc_from_path.title == "Mock Paper"
    assert doc_from_path.metadata["filename"] == "/tmp/paper.pdf"


def test_extracted_document_defaults_and_serialization() -> None:
    """Verify ExtractedDocument default attributes and Pydantic serialization."""
    doc = ExtractedDocument()

    assert doc.title is None
    assert doc.abstract is None
    assert doc.methodology is None
    assert doc.experiments is None
    assert doc.results is None
    assert doc.full_text == ""
    assert doc.sections == {}
    assert doc.metadata == {}

    data = doc.model_dump()
    assert "sections" in data
    assert "metadata" in data
    assert data["full_text"] == ""
