"""Input validation and security guardrails for ReproCheck.

Provides checks for uploaded file size, format integrity, and lightweight
prompt injection scanning for research paper content.
"""

import re
from app.config import get_settings

settings = get_settings()

# Known adversarial prompt injection patterns in submitted text
PROMPT_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:rules|guidelines|instructions?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|jailbroken|dan)\b", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:\s*override", re.IGNORECASE),
    re.compile(r"output\s+[\"']?(?:accepted|well\s+documented)[\"']?\s+without\s+(?:review|evaluat)", re.IGNORECASE),
    re.compile(r"bypass\s+(?:methodology\s+)?review", re.IGNORECASE),
]


class GuardrailError(ValueError):
    """Base exception for input guardrail validation failures."""
    pass


class FileSizeLimitExceededError(GuardrailError):
    """Raised when an uploaded document exceeds the maximum permitted byte size."""
    pass


class InvalidFileFormatError(GuardrailError):
    """Raised when an uploaded file is not a supported format or has invalid headers."""
    pass


class PromptInjectionDetectedError(GuardrailError):
    """Raised when submitted text contains prompt injection or adversarial directives."""
    pass


def validate_file_upload(
    filename: str | None,
    content: bytes,
    max_size_bytes: int | None = None,
) -> None:
    """Validate uploaded document file size and format.

    Args:
        filename: Original file name.
        content: Raw binary payload of the file.
        max_size_bytes: Optional size limit in bytes (defaults to settings).

    Raises:
        FileSizeLimitExceededError: If content length exceeds size limit.
        InvalidFileFormatError: If file is not a valid PDF.
    """
    limit = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES

    if not content:
        raise InvalidFileFormatError("Uploaded file is empty.")

    if len(content) > limit:
        max_mb = limit / (1024 * 1024)
        raise FileSizeLimitExceededError(
            f"File size ({len(content)} bytes) exceeds maximum limit of {max_mb:.0f} MB."
        )

    # Check filename extension
    if filename and not filename.lower().endswith(".pdf"):
        raise InvalidFileFormatError(f"Unsupported file format: '{filename}'. Only PDF files are supported.")

    # Check PDF magic bytes (%PDF-)
    if not content.startswith(b"%PDF-"):
        raise InvalidFileFormatError("File does not have a valid PDF header.")


def validate_text_input(text: str, max_chars: int = 500_000) -> str:
    """Validate pasted methodology or user text input.

    Args:
        text: Input string.
        max_chars: Maximum permitted character length.

    Returns:
        str: Cleaned and stripped text.

    Raises:
        InvalidFileFormatError: If text is empty or exceeds character limits.
    """
    cleaned = text.strip()
    if not cleaned:
        raise InvalidFileFormatError("Input text cannot be empty.")

    if len(cleaned) > max_chars:
        raise FileSizeLimitExceededError(f"Input text exceeds maximum allowed length of {max_chars} characters.")

    return cleaned


def scan_prompt_injection(content: str) -> list[str]:
    """Scan paper content or user prompt for known adversarial injection patterns.

    Args:
        content: Text content to inspect.

    Returns:
        list[str]: Matched risk flags or pattern descriptions.
    """
    detected_patterns: list[str] = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = pattern.search(content)
        if match:
            detected_patterns.append(match.group(0))

    return detected_patterns


def check_content_safety(content: str) -> None:
    """Scan content and raise PromptInjectionDetectedError if adversarial text is found.

    Args:
        content: Text content to check.

    Raises:
        PromptInjectionDetectedError: If an injection pattern is detected.
    """
    risks = scan_prompt_injection(content)
    if risks:
        raise PromptInjectionDetectedError(
            f"Potential prompt injection pattern detected: '{risks[0]}'."
        )
