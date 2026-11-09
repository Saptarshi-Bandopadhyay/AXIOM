"""Endpoints for evidence-grounded question answering on review sessions."""

from fastapi import APIRouter, Depends
from app.api.deps import get_session_or_404, get_workflow_service
from app.models.session import ReviewSession
from app.schemas.qna import AnswerResponse, QuestionRequest
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/sessions/{session_id}/qna", tags=["Grounded Q&A"])


@router.post("", response_model=AnswerResponse)
async def ask_grounded_question(
    request: QuestionRequest,
    session: ReviewSession = Depends(get_session_or_404),
    workflow: WorkflowService = Depends(get_workflow_service),
) -> AnswerResponse:
    """Submit a question to the evidence-grounded reviewer assistant."""
    answer = await workflow.answer_question(session.id, request.question)
    return AnswerResponse(question=request.question, answer=answer)
