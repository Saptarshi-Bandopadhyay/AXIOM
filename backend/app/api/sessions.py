"""Endpoints for paper submission (PDF upload and pasted methodology) and session retrieval."""

import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import (
    get_db_session,
    get_extractor_service,
    get_session_or_404,
    get_storage_service,
    get_workflow_service,
)
from app.core.guardrails import (
    GuardrailError,
    check_content_safety,
    validate_file_upload,
    validate_text_input,
)
from app.interfaces.extractor import ExtractorInterface
from app.interfaces.storage import StorageInterface
from app.models.session import InputType, Paper, ReviewSession, SessionStatus
from app.schemas.session import SessionCreateTextRequest, SessionResponse
from app.services.workflow_service import WorkflowService
from app.workflows.state import ReviewGraphState

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/upload", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Academic research paper PDF file."),
    primary_research_type: str | None = Form(default=None, description="Optional manual research paradigm."),
    db: AsyncSession = Depends(get_db_session),
    storage: StorageInterface = Depends(get_storage_service),
    extractor: ExtractorInterface = Depends(get_extractor_service),
    workflow: WorkflowService = Depends(get_workflow_service),
) -> ReviewSession:
    """Upload a PDF research paper, extract sections, and initiate review workflow."""
    content = await file.read()

    # Guardrail checks: file format and size
    try:
        validate_file_upload(file.filename, content)
    except GuardrailError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Extract text and sections using PyMuPDF
    try:
        doc = await extractor.extract_from_bytes(content, filename=file.filename)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract document contents: {exc}",
        )

    # Guardrail checks: prompt injection scan on extracted methodology
    try:
        check_content_safety(doc.methodology)
    except GuardrailError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Save PDF to storage
    stored_filename = f"papers/{uuid.uuid4()}_{file.filename}"
    file_path = await storage.save(stored_filename, content)

    # Persist session and paper in database
    session_id = uuid.uuid4()
    review_session = ReviewSession(
        id=session_id,
        status=SessionStatus.EXTRACTING,
        input_type=InputType.PDF_UPLOAD,
    )
    paper = Paper(
        session_id=session_id,
        original_filename=file.filename,
        file_path=file_path,
        title=doc.title,
        abstract_text=doc.abstract,
        methodology_text=doc.methodology,
        experiments_text=doc.experiments,
        results_text=doc.results,
        full_text=doc.full_text,
        primary_research_type=primary_research_type,
    )
    review_session.paper = paper

    db.add(review_session)
    await db.commit()
    await db.refresh(review_session)

    # Enqueue background workflow execution from START to checklist interrupt
    initial_state: ReviewGraphState = {
        "session_id": str(session_id),
        "title": doc.title,
        "abstract_text": doc.abstract,
        "methodology_text": doc.methodology,
        "experiments_text": doc.experiments,
        "results_text": doc.results,
        "full_text": doc.full_text,
        "input_type": InputType.PDF_UPLOAD.value,
        "primary_research_type": primary_research_type,
    }
    background_tasks.add_task(workflow.execute_initial_phase, session_id, initial_state)

    return review_session


@router.post("/paste", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def submit_pasted_methodology(
    request: SessionCreateTextRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    workflow: WorkflowService = Depends(get_workflow_service),
) -> ReviewSession:
    """Submit pasted methodology text and initiate review workflow."""
    # Guardrail checks: validate text length and scan for prompt injection
    try:
        cleaned_text = validate_text_input(request.methodology_text)
        check_content_safety(cleaned_text)
    except GuardrailError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    session_id = uuid.uuid4()
    review_session = ReviewSession(
        id=session_id,
        status=SessionStatus.EXTRACTING,
        input_type=InputType.PASTED_TEXT,
    )
    paper = Paper(
        session_id=session_id,
        title=request.title,
        methodology_text=cleaned_text,
        primary_research_type=request.primary_research_type,
    )
    review_session.paper = paper

    db.add(review_session)
    await db.commit()
    await db.refresh(review_session)

    initial_state: ReviewGraphState = {
        "session_id": str(session_id),
        "title": request.title,
        "methodology_text": cleaned_text,
        "input_type": InputType.PASTED_TEXT.value,
        "primary_research_type": request.primary_research_type,
    }
    background_tasks.add_task(workflow.execute_initial_phase, session_id, initial_state)

    return review_session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_details(
    session: ReviewSession = Depends(get_session_or_404),
) -> ReviewSession:
    """Retrieve review session status and paper details."""
    return session
