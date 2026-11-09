"""Integration tests verifying live PostgreSQL operations and cascade integrity."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from app.config import get_settings
from app.models.session import InputType, Paper, ReviewSession, SessionStatus

settings = get_settings()


async def test_live_postgres_ping() -> None:
    """Verify live connectivity to PostgreSQL using an isolated async engine."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    try:
        from app.core.database import check_db_connection
        is_connected = await check_db_connection(target_engine=engine)
        assert is_connected is True, "PostgreSQL must be connected"
    finally:
        await engine.dispose()


async def test_session_and_paper_crud_lifecycle() -> None:
    """Verify full CRUD lifecycle and CASCADE deletion in live PostgreSQL database."""
    # Use NullPool so connections are cleanly closed within this test's event loop
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    session_id = uuid.uuid4()

    try:
        async with session_factory() as session:
            # Create ReviewSession
            review_session = ReviewSession(
                id=session_id,
                status=SessionStatus.PENDING_INPUT,
                input_type=InputType.PDF_UPLOAD,
            )
            # Create Paper associated with ReviewSession
            paper = Paper(
                session_id=session_id,
                title="Attention Is All You Need",
                methodology_text="Model architecture uses self-attention mechanisms without recurrence.",
                primary_research_type="Model Architecture",
                secondary_research_types=["Attention Mechanisms"],
            )
            review_session.paper = paper
            session.add(review_session)
            await session.commit()

        # Query inserted session and paper
        async with session_factory() as session:
            stmt = select(ReviewSession).where(ReviewSession.id == session_id)
            result = await session.execute(stmt)
            fetched_session = result.scalar_one_or_none()

            assert fetched_session is not None
            assert fetched_session.status == SessionStatus.PENDING_INPUT
            assert fetched_session.paper is not None
            assert fetched_session.paper.title == "Attention Is All You Need"
            assert fetched_session.paper.secondary_research_types == ["Attention Mechanisms"]

            # Clean up: delete session and verify paper is cascade deleted
            await session.delete(fetched_session)
            await session.commit()

        # Verify paper is cascade deleted
        async with session_factory() as session:
            paper_stmt = select(Paper).where(Paper.session_id == session_id)
            paper_result = await session.execute(paper_stmt)
            assert paper_result.scalar_one_or_none() is None
    finally:
        await engine.dispose()
