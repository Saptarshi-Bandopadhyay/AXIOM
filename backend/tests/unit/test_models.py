"""Tests for ReviewSession and Paper models."""

import uuid
from app.models.session import InputType, Paper, ReviewSession, SessionStatus


def test_models_relationship() -> None:
    session_id = uuid.uuid4()
    session = ReviewSession(
        id=session_id,
        status=SessionStatus.PENDING_INPUT,
        input_type=InputType.PDF_UPLOAD,
    )
    paper = Paper(session_id=session_id, methodology_text="method")
    session.paper = paper

    assert session.status == SessionStatus.PENDING_INPUT
    assert session.paper.methodology_text == "method"
    assert paper.session is session
