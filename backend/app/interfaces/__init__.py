"""Interfaces package defining abstract system contracts."""

from app.interfaces.extractor import ExtractedDocument, ExtractorInterface
from app.interfaces.storage import StorageInterface

__all__ = [
    "StorageInterface",
    "ExtractorInterface",
    "ExtractedDocument",
]
