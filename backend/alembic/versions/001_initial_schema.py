"""create review_sessions and papers tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-09 17:30:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers, used by Alembic
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create review_sessions and papers tables with indices and foreign keys."""
    # --------------------------------------------------------------------------
    # 1. review_sessions table
    # --------------------------------------------------------------------------
    op.create_table(
        "review_sessions",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Unique identifier for the review session.",
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=True,
            comment="Optional identifier of the owning user for future auth support.",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            comment="Current execution lifecycle status of the session.",
        ),
        sa.Column(
            "input_type",
            sa.String(length=20),
            nullable=False,
            comment="Method used to submit the research paper material.",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Diagnostic error details if the review workflow encounters a failure.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="UTC timestamp when the record was created.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="UTC timestamp when the record was last modified.",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_review_sessions_user_id"),
        "review_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_review_sessions_status"),
        "review_sessions",
        ["status"],
        unique=False,
    )

    # --------------------------------------------------------------------------
    # 2. papers table
    # --------------------------------------------------------------------------
    op.create_table(
        "papers",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Unique identifier for the paper record.",
        ),
        sa.Column(
            "session_id",
            sa.Uuid(),
            nullable=False,
            comment="Foreign key linking to parent review session.",
        ),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=True,
            comment="Original uploaded filename of the PDF paper.",
        ),
        sa.Column(
            "file_path",
            sa.String(length=512),
            nullable=True,
            comment="Local filesystem storage path for the uploaded PDF.",
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=True,
            comment="Extracted or detected title of the research paper.",
        ),
        sa.Column(
            "abstract_text",
            sa.Text(),
            nullable=True,
            comment="Extracted abstract section text.",
        ),
        sa.Column(
            "methodology_text",
            sa.Text(),
            nullable=False,
            comment="Extracted or pasted methodology section text (primary review context).",
        ),
        sa.Column(
            "experiments_text",
            sa.Text(),
            nullable=True,
            comment="Extracted experiments and evaluation setup section text.",
        ),
        sa.Column(
            "results_text",
            sa.Text(),
            nullable=True,
            comment="Extracted findings and results section text.",
        ),
        sa.Column(
            "full_text",
            sa.Text(),
            nullable=True,
            comment="Complete text content extracted from the submitted PDF document.",
        ),
        sa.Column(
            "primary_research_type",
            sa.String(length=100),
            nullable=True,
            comment="Primary identified research paradigm (e.g., RAG, Agents, Fine-tuning).",
        ),
        sa.Column(
            "secondary_research_types",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            comment="Secondary or auxiliary research categories identified in the paper.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="UTC timestamp when the record was created.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="UTC timestamp when the record was last modified.",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["review_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_index(
        op.f("ix_papers_session_id"),
        "papers",
        ["session_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_papers_primary_research_type"),
        "papers",
        ["primary_research_type"],
        unique=False,
    )


def downgrade() -> None:
    """Drop papers and review_sessions tables."""
    op.drop_index(op.f("ix_papers_primary_research_type"), table_name="papers")
    op.drop_index(op.f("ix_papers_session_id"), table_name="papers")
    op.drop_table("papers")
    op.drop_index(op.f("ix_review_sessions_status"), table_name="review_sessions")
    op.drop_index(op.f("ix_review_sessions_user_id"), table_name="review_sessions")
    op.drop_table("review_sessions")
