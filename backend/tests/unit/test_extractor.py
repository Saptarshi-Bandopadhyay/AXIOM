"""Unit tests for PyMuPDFExtractor."""

from pathlib import Path
import pytest
import pymupdf
from app.services.pymupdf_extractor import PyMuPDFExtractor


def _create_sample_pdf_bytes() -> bytes:
    """Helper creating an in-memory sample 2-page academic PDF with sections."""
    doc = pymupdf.open()

    # Page 1: Title, Abstract, Methodology
    page1 = doc.new_page(width=595, height=842)
    text_p1 = (
        "Efficient RAG Architectures for Research Review\n\n"
        "Abstract\n"
        "We present a novel approach to evaluating academic methodologies.\n\n"
        "1. Introduction\n"
        "Modern language models require thorough methodological evaluation.\n\n"
        "3. Methodology\n"
        "Our system retrieves documents using BM25 and dense bi-encoder embeddings.\n"
        "Chunk size is fixed to 512 tokens with 50 token overlap.\n"
    )
    page1.insert_text((50, 72), text_p1, fontsize=11)

    # Page 2: Experiments, Results
    page2 = doc.new_page(width=595, height=842)
    text_p2 = (
        "4. Experiments\n"
        "We evaluate on 50 arXiv research papers across five domains.\n"
        "Hardware consists of 4x NVIDIA A100 GPUs running vLLM.\n\n"
        "5. Results\n"
        "Our method achieves 92.4% precision on citation grounding.\n\n"
        "References\n"
        "[1] Vaswani et al. Attention is All You Need. 2017.\n"
    )
    page2.insert_text((50, 72), text_p2, fontsize=11)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


async def test_extract_from_bytes_parses_sections() -> None:
    """Verify section segmentation from in-memory PDF bytes."""
    extractor = PyMuPDFExtractor()
    pdf_bytes = _create_sample_pdf_bytes()

    doc = await extractor.extract_from_bytes(pdf_bytes, filename="sample_paper.pdf")

    assert doc.title is not None
    assert "Efficient RAG Architectures" in doc.title
    assert doc.abstract is not None
    assert "novel approach to evaluating academic methodologies" in doc.abstract
    assert doc.methodology is not None
    assert "dense bi-encoder embeddings" in doc.methodology
    assert doc.experiments is not None
    assert "4x NVIDIA A100 GPUs" in doc.experiments
    assert doc.results is not None
    assert "92.4% precision" in doc.results
    assert doc.metadata["page_count"] == 2
    assert doc.metadata["filename"] == "sample_paper.pdf"


async def test_extract_from_path(tmp_path: Path) -> None:
    """Verify extracting from a physical PDF file path on disk."""
    extractor = PyMuPDFExtractor()
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(_create_sample_pdf_bytes())

    doc = await extractor.extract_from_path(str(pdf_path))
    assert doc.metadata["page_count"] == 2
    assert doc.metadata["filename"] == "paper.pdf"
    assert "BM25" in doc.methodology


async def test_empty_content_raises_value_error() -> None:
    """Verify empty byte payload raises ValueError."""
    extractor = PyMuPDFExtractor()
    with pytest.raises(ValueError) as exc:
        await extractor.extract_from_bytes(b"")
    assert "Document content is empty" in str(exc.value)


async def test_missing_file_path_raises_file_not_found() -> None:
    """Verify non-existent path raises FileNotFoundError."""
    extractor = PyMuPDFExtractor()
    with pytest.raises(FileNotFoundError):
        await extractor.extract_from_path("/non/existent/file.pdf")
