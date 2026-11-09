"""Endpoints for checklist retrieval, editing, and user approval."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.api.deps import get_session_or_404, get_workflow_service
from app.models.session import ReviewSession, SessionStatus
from app.schemas.checklist import ChecklistApprovalRequest, ChecklistResponse
from app.services.workflow_service import WorkflowService
from app.workflows.state import ChecklistItem

router = APIRouter(prefix="/sessions/{session_id}/checklist", tags=["Checklists"])


@router.get("", response_model=ChecklistResponse)
async def get_session_checklist(
    session: ReviewSession = Depends(get_session_or_404),
    workflow: WorkflowService = Depends(get_workflow_service),
) -> ChecklistResponse:
    """Retrieve the generated or approved review checklist for a session."""
    snapshot = await workflow.get_state_snapshot(session.id)
    raw_checklist = snapshot.get("checklist", [])

    items = [ChecklistItem(**item) for item in raw_checklist]
    is_approved = snapshot.get("checklist_approved", False) or session.status in (
        SessionStatus.REVIEWING,
        SessionStatus.COMPLETED,
    )

    return ChecklistResponse(
        session_id=session.id,
        status=session.status,
        checklist=items,
        approved=is_approved,
    )


@router.post("/approve", response_model=ChecklistResponse)
async def approve_session_checklist(
    request: ChecklistApprovalRequest,
    background_tasks: BackgroundTasks,
    session: ReviewSession = Depends(get_session_or_404),
    workflow: WorkflowService = Depends(get_workflow_service),
) -> ChecklistResponse:
    """Submit approved and edited checklist criteria and resume review execution."""
    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review workflow for this session has already completed.",
        )

    # Resume the workflow state machine in the background
    serialized_checklist = [item.model_dump() for item in request.checklist]
    background_tasks.add_task(
        workflow.resume_with_approval, session.id, serialized_checklist
    )

    return ChecklistResponse(
        session_id=session.id,
        status=SessionStatus.REVIEWING,
        checklist=request.checklist,
        approved=True,
    )
