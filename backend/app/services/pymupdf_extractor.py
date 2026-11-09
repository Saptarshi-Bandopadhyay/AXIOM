"""PyMuPDF document extractor implementation with section segmentation."""

import asyncio
import re
from pathlib import Path
import pymupdf
from app.interfaces.extractor import ExtractedDocument, ExtractorInterface

# Regular expression matching standard academic section headings
SECTION_HEADING_PATTERN = re.compile(
    r"^(?:\d+\.?\s*)?(abstract|methodology|method|approach|experiments|evaluation|results)\b",
    re.IGNORECASE,
)

# Canonical mapping for common heading variations
HEADER_CANONICAL_MAP = {
    "method": "methodology",
    "approach": "methodology",
    "evaluation": "experiments",
}


class PyMuPDFExtractor(ExtractorInterface):
    """Extracts text and key academic sections from PDF documents using PyMuPDF."""

    def _parse_document(
        self, doc: pymupdf.Document, filename: str | None = None
    ) -> ExtractedDocument:
        """Parse PDF document into full text and structured sections."""
        # sort=True ensures correct reading order for multi-column academic layouts
        full_text = "\n\n".join(page.get_text("text", sort=True) for page in doc).strip()
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        # Heuristic: Title is typically in the first 1-2 lines before abstract
        title = " ".join(lines[:2]) if lines else None

        # Segment document lines into section buckets
        sections: dict[str, list[str]] = {}
        current_section = "body"

        for line in lines:
            match = SECTION_HEADING_PATTERN.match(line)
            if match and len(line) < 60:
                header = match.group(1).lower()
                current_section = HEADER_CANONICAL_MAP.get(header, header)
            sections.setdefault(current_section, []).append(line)

        def get_section_text(*names: str) -> str | None:
            """Retrieve the text of the first matching section name."""
            for name in names:
                if name in sections:
                    return "\n".join(sections[name]).strip()
            return None

        # Fall back to full text if no dedicated methodology section is recognized
        methodology = get_section_text("methodology") or full_text

        return ExtractedDocument(
            title=title,
            abstract=get_section_text("abstract"),
            methodology=methodology,
            experiments=get_section_text("experiments"),
            results=get_section_text("results"),
            full_text=full_text,
            sections={name: "\n".join(text_lines).strip() for name, text_lines in sections.items()},
            metadata={"page_count": len(doc), "filename": filename},
        )

    async def extract_from_bytes(
        self, content: bytes, filename: str | None = None
    ) -> ExtractedDocument:
        """Extract text and sections from in-memory PDF bytes."""
        if not content:
            raise ValueError("Document content is empty")

        def _extract() -> ExtractedDocument:
            with pymupdf.open(stream=content, filetype="pdf") as doc:
                return self._parse_document(doc, filename=filename)

        return await asyncio.to_thread(_extract)

    async def extract_from_path(self, file_path: str) -> ExtractedDocument:
        """Extract text and sections from a physical PDF file path."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        def _extract() -> ExtractedDocument:
            with pymupdf.open(file_path) as doc:
                return self._parse_document(doc, filename=path.name)

        return await asyncio.to_thread(_extract)
