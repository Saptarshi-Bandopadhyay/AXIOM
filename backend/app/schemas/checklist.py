"""Pydantic schemas for checklist inspection, editing, and approval."""

import uuid
from pydantic import BaseModel, Field
from app.models.session import SessionStatus
from app.workflows.state import ChecklistItem


class ChecklistApprovalRequest(BaseModel):
    """Payload for submitting approved and edited checklist criteria."""

    checklist: list[ChecklistItem] = Field(min_length=1, description="Approved and customized checklist criteria.")


class ChecklistResponse(BaseModel):
    """Structured response containing the candidate or approved checklist."""

    session_id: uuid.UUID
    status: SessionStatus
    checklist: list[ChecklistItem]
    approved: bool = False
