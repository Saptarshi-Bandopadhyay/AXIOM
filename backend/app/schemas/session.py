"""Pydantic schemas for review session creation and responses."""

from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.session import InputType, SessionStatus


class SessionCreateTextRequest(BaseModel):
    """Payload for submitting pasted methodology text."""

    methodology_text: str = Field(min_length=10, description="Raw methodology or approach text.")
    title: str | None = Field(default=None, description="Optional title of the paper.")
    primary_research_type: str | None = Field(default=None, description="Optional user-selected research paradigm.")


class PaperResponse(BaseModel):
    """Structured representation of paper metadata and sections."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    original_filename: str | None
    primary_research_type: str | None
    secondary_research_types: list[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    """Response returned upon session creation or status retrieval."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: SessionStatus
    input_type: InputType
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    paper: PaperResponse | None = None
