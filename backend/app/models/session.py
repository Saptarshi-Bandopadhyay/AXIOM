"""Database ORM models for review sessions and paper submissions.

Defines ReviewSession and Paper entities with modern SQLAlchemy 2.0 typing,
lifecycle statuses, input types, and relationship cascades.
"""

from enum import Enum
import uuid
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.models.base import Base, TimestampMixin


class SessionStatus(str, Enum):
    """Lifecycle status states of a research paper review session."""

    PENDING_INPUT = "PENDING_INPUT"
    EXTRACTING = "EXTRACTING"
    CLASSIFYING = "CLASSIFYING"
    AWAITING_CHECKLIST_APPROVAL = "AWAITING_CHECKLIST_APPROVAL"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InputType(str, Enum):
    """Supported input submission types."""

    PDF_UPLOAD = "PDF_UPLOAD"
    PASTED_TEXT = "PASTED_TEXT"


class ReviewSession(Base, TimestampMixin):
    """ReviewSession entity tracking review state, configuration, and paper linkage."""

    __tablename__ = "review_sessions"

    # Unique session identifier (UUID primary key)
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the review session.",
    )

    # Optional user association for future authentication integration (ADR-007)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
        comment="Optional identifier of the owning user for future auth support.",
    )

    # Current execution status of the review workflow
    status: Mapped[SessionStatus] = mapped_column(
        String(50),
        default=SessionStatus.PENDING_INPUT,
        nullable=False,
        index=True,
        comment="Current execution lifecycle status of the session.",
    )

    # Type of paper content submitted (PDF file vs pasted text)
    input_type: Mapped[InputType] = mapped_column(
        String(20),
        nullable=False,
        comment="Method used to submit the research paper material.",
    )

    # Error details if workflow status transitions to FAILED
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Diagnostic error details if the review workflow encounters a failure.",
    )

    # One-to-one relationship to submitted paper entity
    paper: Mapped["Paper | None"] = relationship(
        "Paper",
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    def __init__(self, **kwargs):
        """Initialize ReviewSession with UUID and default status if omitted."""
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "status" not in kwargs:
            kwargs["status"] = SessionStatus.PENDING_INPUT
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<ReviewSession(id={self.id}, status='{self.status}', input_type='{self.input_type}')>"


class Paper(Base, TimestampMixin):
    """Paper entity containing extracted sections, classifications, and text data."""

    __tablename__ = "papers"

    # Unique paper record identifier
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the paper record.",
    )

    # Foreign key referencing parent review session
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key linking to parent review session.",
    )

    # File storage references (applicable for PDF_UPLOAD input type)
    original_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Original uploaded filename of the PDF paper.",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Local filesystem storage path for the uploaded PDF.",
    )

    # Extracted paper sections
    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted or detected title of the research paper.",
    )
    abstract_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted abstract section text.",
    )
    methodology_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Extracted or pasted methodology section text (primary review context).",
    )
    experiments_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted experiments and evaluation setup section text.",
    )
    results_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Extracted findings and results section text.",
    )
    full_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Complete text content extracted from the submitted PDF document.",
    )

    # Research paradigm classification results
    primary_research_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Primary identified research paradigm (e.g., RAG, Agents, Fine-tuning).",
    )
    secondary_research_types: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
        comment="Secondary or auxiliary research categories identified in the paper.",
    )

    # Back-reference relationship to parent session
    session: Mapped["ReviewSession"] = relationship(
        "ReviewSession",
        back_populates="paper",
    )

    def __init__(self, **kwargs):
        """Initialize Paper with UUID and default secondary types list if omitted."""
        if "id" not in kwargs:
            kwargs["id"] = uuid.uuid4()
        if "secondary_research_types" not in kwargs:
            kwargs["secondary_research_types"] = []
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, session_id={self.session_id}, title='{self.title}')>"
