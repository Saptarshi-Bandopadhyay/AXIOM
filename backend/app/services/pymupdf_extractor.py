"""PyMuPDF document extractor implementation."""

import asyncio
import re
from pathlib import Path
import pymupdf
from app.interfaces.extractor import ExtractedDocument, ExtractorInterface

SECTION_RE = re.compile(
    r"^(?:\d+\.?\s*)?(abstract|methodology|method|approach|experiments|evaluation|results)\b",
    re.IGNORECASE,
)


class PyMuPDFExtractor(ExtractorInterface):
    """Extracts text and basic sections from PDF files."""

    def _parse(self, doc: pymupdf.Document, filename: str | None = None) -> ExtractedDocument:
        full_text = "\n\n".join(page.get_text("text", sort=True) for page in doc).strip()
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]

        title = " ".join(lines[:2]) if lines else None
        sections: dict[str, list[str]] = {}
        current_sec = "body"

        for line in lines:
            m = SECTION_RE.match(line)
            if m and len(line) < 60:
                header = m.group(1).lower()
                header = {"method": "methodology", "approach": "methodology", "evaluation": "experiments"}.get(header, header)
                current_sec = header
            sections.setdefault(current_sec, []).append(line)

        def get_sec(*names: str) -> str | None:
            for name in names:
                if name in sections:
                    return "\n".join(sections[name]).strip()
            return None

        return ExtractedDocument(
            title=title,
            abstract=get_sec("abstract"),
            methodology=get_sec("methodology") or full_text,
            experiments=get_sec("experiments"),
            results=get_sec("results"),
            full_text=full_text,
            sections={k: "\n".join(v).strip() for k, v in sections.items()},
            metadata={"page_count": len(doc), "filename": filename},
        )

    async def extract_from_bytes(self, content: bytes, filename: str | None = None) -> ExtractedDocument:
        if not content:
            raise ValueError("Document content is empty")
        return await asyncio.to_thread(lambda: self._parse(pymupdf.open(stream=content, filetype="pdf"), filename))

    async def extract_from_path(self, file_path: str) -> ExtractedDocument:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        return await asyncio.to_thread(lambda: self._parse(pymupdf.open(file_path), path.name))
