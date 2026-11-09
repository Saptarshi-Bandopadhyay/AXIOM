"""Database models for review sessions and paper submissions."""

from enum import Enum
import uuid
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from app.models.base import Base, TimestampMixin


class SessionStatus(str, Enum):
    PENDING_INPUT = "PENDING_INPUT"
    EXTRACTING = "EXTRACTING"
    CLASSIFYING = "CLASSIFYING"
    AWAITING_CHECKLIST_APPROVAL = "AWAITING_CHECKLIST_APPROVAL"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InputType(str, Enum):
    PDF_UPLOAD = "PDF_UPLOAD"
    PASTED_TEXT = "PASTED_TEXT"


class ReviewSession(Base, TimestampMixin):
    __tablename__ = "review_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    status: Mapped[SessionStatus] = mapped_column(String(50), default=SessionStatus.PENDING_INPUT, index=True)
    input_type: Mapped[InputType] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    paper: Mapped["Paper | None"] = relationship(
        "Paper",
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )


class Paper(Base, TimestampMixin):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("review_sessions.id", ondelete="CASCADE"), unique=True, index=True
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology_text: Mapped[str] = mapped_column(Text, nullable=False)
    experiments_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    results_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_research_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    secondary_research_types: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list
    )

    session: Mapped["ReviewSession"] = relationship("ReviewSession", back_populates="paper")
