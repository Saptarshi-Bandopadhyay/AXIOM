"""PyMuPDF document extractor implementation.

Extracts text from PDF documents with two-column reading order awareness (sort=True)
and segments standard academic sections (Abstract, Methodology, Experiments, Results).
"""

import asyncio
import re
from pathlib import Path
import pymupdf
from app.interfaces.extractor import ExtractedDocument, ExtractorInterface

# Common academic section header patterns
SECTION_PATTERNS = {
    "abstract": re.compile(r"^(?:[0-9\.]*\s*)?abstract\b", re.IGNORECASE),
    "methodology": re.compile(
        r"^(?:[0-9\.]*\s*)?(?:methodology|method|approach|proposed\s+method|system\s+design|architecture)\b",
        re.IGNORECASE,
    ),
    "experiments": re.compile(
        r"^(?:[0-9\.]*\s*)?(?:experiments|experimental\s+setup|evaluation|empirical\s+evaluation)\b",
        re.IGNORECASE,
    ),
    "results": re.compile(
        r"^(?:[0-9\.]*\s*)?(?:results|findings|experimental\s+results|main\s+results)\b",
        re.IGNORECASE,
    ),
    "conclusion": re.compile(
        r"^(?:[0-9\.]*\s*)?(?:conclusion|conclusions|discussion|references)\b",
        re.IGNORECASE,
    ),
}


class PyMuPDFExtractor(ExtractorInterface):
    """Concrete PDF text and section extractor using PyMuPDF."""

    def _extract_sync(self, doc: pymupdf.Document, filename: str | None = None) -> ExtractedDocument:
        """Synchronously extract full text and segment sections from a PyMuPDF Document."""
        page_texts = []
        for page in doc:
            # sort=True ensures reading-order text flow in multi-column layouts
            page_texts.append(page.get_text("text", sort=True))

        full_text = "\n\n".join(page_texts).strip()
        lines = full_text.splitlines()

        # Extract title (first prominent non-empty text before Abstract)
        title = None
        title_candidates = []
        for line in lines[:25]:
            stripped = line.strip()
            if not stripped:
                continue
            if SECTION_PATTERNS["abstract"].match(stripped):
                break
            title_candidates.append(stripped)
        if title_candidates:
            title = " ".join(title_candidates[:2])

        # Segment sections based on heading patterns
        sections: dict[str, list[str]] = {
            "abstract": [],
            "methodology": [],
            "experiments": [],
            "results": [],
            "other": [],
        }
        current_section = "other"

        for line in lines:
            stripped = line.strip()
            matched = False
            for sec_name, pattern in SECTION_PATTERNS.items():
                if pattern.match(stripped) and len(stripped) < 60:
                    current_section = sec_name if sec_name in sections else "other"
                    matched = True
                    break
            if not matched and current_section in sections:
                sections[current_section].append(line)

        # Methodology fallback: if no explicit methodology header, treat full text as context
        methodology = "\n".join(sections["methodology"]).strip() or full_text

        return ExtractedDocument(
            title=title,
            abstract="\n".join(sections["abstract"]).strip() or None,
            methodology=methodology,
            experiments="\n".join(sections["experiments"]).strip() or None,
            results="\n".join(sections["results"]).strip() or None,
            full_text=full_text,
            sections={k: "\n".join(v).strip() for k, v in sections.items() if v},
            metadata={
                "page_count": len(doc),
                "filename": filename,
            },
        )

    async def extract_from_bytes(
        self, content: bytes, filename: str | None = None
    ) -> ExtractedDocument:
        """Extract text and sections from in-memory PDF bytes."""
        if not content:
            raise ValueError("Document content is empty")

        def _run():
            with pymupdf.open(stream=content, filetype="pdf") as doc:
                return self._extract_sync(doc, filename=filename)

        return await asyncio.to_thread(_run)

    async def extract_from_path(self, file_path: str) -> ExtractedDocument:
        """Extract text and sections from a PDF file path."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        def _run():
            with pymupdf.open(file_path) as doc:
                return self._extract_sync(doc, filename=path.name)

        return await asyncio.to_thread(_run)
