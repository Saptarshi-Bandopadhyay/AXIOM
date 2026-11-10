"""Endpoints for review status polling and comprehensive report retrieval."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_session_or_404, get_workflow_service
from app.models.session import ReviewSession, SessionStatus
from app.schemas.review import ReviewReportResponse, ReviewStatusResponse
from app.services.workflow_service import WorkflowService
from app.workflows.state import (
    ChecklistItem,
    InconsistencyItem,
    OverallAssessment,
    ReviewFinding,
)

router = APIRouter(prefix="/sessions/{session_id}", tags=["Reviews"])


@router.get("/status", response_model=ReviewStatusResponse)
async def get_review_status(
    session: ReviewSession = Depends(get_session_or_404),
) -> ReviewStatusResponse:
    """Poll the current lifecycle state of a review session."""
    return ReviewStatusResponse(
        session_id=session.id,
        status=session.status,
        error_message=session.error_message,
    )


@router.get("/report", response_model=ReviewReportResponse)
async def get_review_report(
    session: ReviewSession = Depends(get_session_or_404),
    workflow: WorkflowService = Depends(get_workflow_service),
) -> ReviewReportResponse:
    """Retrieve the completed methodology review report."""
    snapshot = await workflow.get_state_snapshot(session.id)

    raw_checklist = snapshot.get("checklist", [])
    raw_findings = snapshot.get("findings", [])
    raw_inconsistencies = snapshot.get("inconsistencies", [])
    raw_assessment = snapshot.get("overall_assessment")

    checklist = [ChecklistItem(**item) for item in raw_checklist]
    findings = [ReviewFinding(**item) for item in raw_findings]
    inconsistencies = [InconsistencyItem(**item) for item in raw_inconsistencies]
    assessment = OverallAssessment(**raw_assessment) if raw_assessment else None

    # Get paper title and paradigms
    title = snapshot.get("title") or (session.paper.title if session.paper else None)
    primary_type = snapshot.get("primary_research_type") or (
        session.paper.primary_research_type if session.paper else None
    )
    secondary_types = snapshot.get("secondary_research_types") or (
        session.paper.secondary_research_types if session.paper else []
    )

    return ReviewReportResponse(
        session_id=session.id,
        status=session.status,
        title=title,
        primary_research_type=primary_type,
        secondary_research_types=secondary_types,
        checklist=checklist,
        findings=findings,
        inconsistencies=inconsistencies,
        overall_assessment=assessment,
    )


# Top-level route aliases for /reviews/{session_id}
alias_router = APIRouter(prefix="/reviews/{session_id}", tags=["Reviews"])
alias_router.add_api_route("/status", get_review_status, methods=["GET"], response_model=ReviewStatusResponse)
alias_router.add_api_route("/report", get_review_report, methods=["GET"], response_model=ReviewReportResponse)
