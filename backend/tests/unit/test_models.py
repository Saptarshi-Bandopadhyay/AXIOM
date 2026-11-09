"""Unit tests for ReviewSession and Paper ORM models."""

import uuid
from app.models.session import InputType, Paper, ReviewSession, SessionStatus


def test_review_session_defaults_and_initialization() -> None:
    """Verify default field values on a newly instantiated ReviewSession."""
    session = ReviewSession(input_type=InputType.PDF_UPLOAD)

    # Generated or default attributes
    assert session.input_type == InputType.PDF_UPLOAD
    assert session.status == SessionStatus.PENDING_INPUT
    assert session.user_id is None
    assert session.error_message is None
    assert session.paper is None


def test_paper_initialization_and_attributes() -> None:
    """Verify Paper model initialization and default secondary research types."""
    session_id = uuid.uuid4()
    paper = Paper(
        session_id=session_id,
        methodology_text="Detailed methodology text describing experiment setup.",
        primary_research_type="RAG Systems",
        secondary_research_types=["AI Evaluation"],
    )

    assert paper.session_id == session_id
    assert paper.methodology_text == "Detailed methodology text describing experiment setup."
    assert paper.primary_research_type == "RAG Systems"
    assert paper.secondary_research_types == ["AI Evaluation"]
    assert paper.abstract_text is None
    assert paper.experiments_text is None


def test_session_and_paper_relationship_linkage() -> None:
    """Verify bidirectional relationship binding between ReviewSession and Paper."""
    session = ReviewSession(input_type=InputType.PASTED_TEXT)
    paper = Paper(
        session_id=session.id,
        methodology_text="Pasted methodology text for evaluation.",
    )

    # Link entities
    session.paper = paper
    assert paper.session is session
    assert session.paper is paper


def test_session_status_and_input_type_enums() -> None:
    """Verify that all specified lifecycle states and input formats exist in enums."""
    assert SessionStatus.PENDING_INPUT.value == "PENDING_INPUT"
    assert SessionStatus.EXTRACTING.value == "EXTRACTING"
    assert SessionStatus.CLASSIFYING.value == "CLASSIFYING"
    assert SessionStatus.AWAITING_CHECKLIST_APPROVAL.value == "AWAITING_CHECKLIST_APPROVAL"
    assert SessionStatus.REVIEWING.value == "REVIEWING"
    assert SessionStatus.COMPLETED.value == "COMPLETED"
    assert SessionStatus.FAILED.value == "FAILED"

    assert InputType.PDF_UPLOAD.value == "PDF_UPLOAD"
    assert InputType.PASTED_TEXT.value == "PASTED_TEXT"


def test_model_repr_formatting() -> None:
    """Verify human-readable __repr__ strings for logging and debugging."""
    session_id = uuid.uuid4()
    session = ReviewSession(
        id=session_id,
        status=SessionStatus.REVIEWING,
        input_type=InputType.PDF_UPLOAD,
    )
    paper = Paper(
        id=uuid.uuid4(),
        session_id=session_id,
        title="Test Paper Title",
        methodology_text="Methodology",
    )

    session_repr = repr(session)
    paper_repr = repr(paper)

    assert str(session_id) in session_repr
    assert "REVIEWING" in session_repr
    assert "PDF_UPLOAD" in session_repr

    assert "Test Paper Title" in paper_repr
    assert str(session_id) in paper_repr
