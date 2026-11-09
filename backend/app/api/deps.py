"""FastAPI dependency injection providers for database, services, and session lookup."""

from collections.abc import AsyncGenerator
import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.interfaces.extractor import ExtractorInterface
from app.interfaces.storage import StorageInterface
from app.models.session import ReviewSession
from app.services.local_storage import LocalStorageService
from app.services.pymupdf_extractor import PyMuPDFExtractor
from app.services.workflow_service import WorkflowService, workflow_service


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active database session."""
    async for session in get_db():
        yield session


def get_storage_service() -> StorageInterface:
    """Dependency providing file storage interface."""
    return LocalStorageService()


def get_extractor_service() -> ExtractorInterface:
    """Dependency providing document extraction interface."""
    return PyMuPDFExtractor()


def get_workflow_service() -> WorkflowService:
    """Dependency providing workflow execution service."""
    return workflow_service


async def get_session_or_404(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ReviewSession:
    """Retrieve review session by ID or raise HTTP 404."""
    stmt = select(ReviewSession).where(ReviewSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review session '{session_id}' not found.",
        )

    return session
