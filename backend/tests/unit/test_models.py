"""Unit tests for ReviewSession and Paper ORM models."""

import uuid
from app.models.session import InputType, Paper, ReviewSession, SessionStatus


def test_review_session_and_paper_relationship() -> None:
    """Verify ReviewSession and Paper instantiation and relationship wiring."""
    session_id = uuid.uuid4()
    session = ReviewSession(
        id=session_id,
        status=SessionStatus.PENDING_INPUT,
        input_type=InputType.PDF_UPLOAD,
    )
    paper = Paper(
        session_id=session_id,
        title="Sample Paper Title",
        methodology_text="Detailed methodology description.",
        primary_research_type="Empirical Evaluation",
    )
    session.paper = paper

    assert session.status == SessionStatus.PENDING_INPUT
    assert session.paper.title == "Sample Paper Title"
    assert session.paper.methodology_text == "Detailed methodology description."
    assert paper.session is session
