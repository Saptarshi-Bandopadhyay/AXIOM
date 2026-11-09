"""Tests for PyMuPDFExtractor."""

from pathlib import Path
import pytest
import pymupdf
from app.services.pymupdf_extractor import PyMuPDFExtractor


def _make_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "Sample Paper Title\n\nAbstract\nPaper abstract.\n\nMethodology\nOur method.\n\nExperiments\nTest setup.",
    )
    b = doc.tobytes()
    doc.close()
    return b


async def test_extractor_from_bytes() -> None:
    doc = await PyMuPDFExtractor().extract_from_bytes(_make_pdf(), filename="paper.pdf")
    assert "Sample Paper Title" in (doc.title or "")
    assert "Paper abstract" in (doc.abstract or "")
    assert "Our method" in doc.methodology
    assert "Test setup" in (doc.experiments or "")
    assert doc.metadata["page_count"] == 1


async def test_extractor_from_path(tmp_path: Path) -> None:
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(_make_pdf())
    doc = await PyMuPDFExtractor().extract_from_path(str(pdf_path))
    assert "Our method" in doc.methodology


async def test_extractor_errors(tmp_path: Path) -> None:
    extractor = PyMuPDFExtractor()
    with pytest.raises(ValueError):
        await extractor.extract_from_bytes(b"")
    with pytest.raises(FileNotFoundError):
        await extractor.extract_from_path("/non/existent/file.pdf")
