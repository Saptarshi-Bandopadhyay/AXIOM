"""Pydantic schemas for review status polling and report retrieval."""

import uuid
from pydantic import BaseModel, Field
from app.models.session import SessionStatus
from app.workflows.state import (
    ChecklistItem,
    InconsistencyItem,
    OverallAssessment,
    ReviewFinding,
)


class ReviewStatusResponse(BaseModel):
    """Status polling response for an ongoing review session."""

    session_id: uuid.UUID
    status: SessionStatus
    error_message: str | None = None


class ReviewReportResponse(BaseModel):
    """Complete methodology review report containing findings, evidence, and assessment."""

    session_id: uuid.UUID
    status: SessionStatus
    title: str | None = None
    primary_research_type: str | None = None
    secondary_research_types: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    findings: list[ReviewFinding] = Field(default_factory=list)
    inconsistencies: list[InconsistencyItem] = Field(default_factory=list)
    overall_assessment: OverallAssessment | None = None
