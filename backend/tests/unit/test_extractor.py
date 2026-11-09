"""Unit tests for PyMuPDFExtractor document parsing and section extraction."""

from pathlib import Path
import pytest
import pymupdf
from app.services.pymupdf_extractor import PyMuPDFExtractor


def _create_sample_pdf_bytes() -> bytes:
    """Create a minimal in-memory PDF with standard academic sections."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    sample_text = (
        "Efficient RAG Architectures for Research Review\n\n"
        "Abstract\n"
        "We present an evaluation framework for academic methodology.\n\n"
        "Methodology\n"
        "Our pipeline uses dense bi-encoder embeddings with BM25 ranking.\n\n"
        "Experiments\n"
        "We evaluate on 50 arXiv papers using 4x NVIDIA A100 GPUs.\n\n"
        "Results\n"
        "The model achieves 92.4% precision on citation grounding.\n"
    )
    page.insert_text((50, 72), sample_text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


async def test_extract_from_bytes_parses_sections() -> None:
    """Verify that PyMuPDFExtractor parses in-memory PDF bytes into structured sections."""
    extractor = PyMuPDFExtractor()
    pdf_bytes = _create_sample_pdf_bytes()

    doc = await extractor.extract_from_bytes(pdf_bytes, filename="sample.pdf")

    assert doc.title is not None
    assert "Efficient RAG Architectures" in doc.title
    assert doc.abstract is not None
    assert "evaluation framework" in doc.abstract
    assert "dense bi-encoder embeddings" in doc.methodology
    assert doc.experiments is not None
    assert "4x NVIDIA A100 GPUs" in doc.experiments
    assert doc.results is not None
    assert "92.4% precision" in doc.results
    assert doc.metadata["page_count"] == 1
    assert doc.metadata["filename"] == "sample.pdf"


async def test_extract_from_file_path(tmp_path: Path) -> None:
    """Verify extracting sections from a physical PDF file path on disk."""
    extractor = PyMuPDFExtractor()
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(_create_sample_pdf_bytes())

    doc = await extractor.extract_from_path(str(pdf_path))

    assert "dense bi-encoder embeddings" in doc.methodology
    assert doc.metadata["filename"] == "paper.pdf"


async def test_extractor_error_handling(tmp_path: Path) -> None:
    """Verify extractor error behavior for empty bytes and missing files."""
    extractor = PyMuPDFExtractor()

    with pytest.raises(ValueError) as exc_info:
        await extractor.extract_from_bytes(b"")
    assert "Document content is empty" in str(exc_info.value)

    with pytest.raises(FileNotFoundError):
        await extractor.extract_from_path("/non/existent/path/paper.pdf")
