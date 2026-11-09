"""Service coordinating review workflow execution, checkpointing, and state queries."""

import logging
from typing import Any
import uuid
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.session import ReviewSession, SessionStatus
from app.workflows.graph import create_review_workflow
from app.workflows.nodes.qna import answer_grounded_question
from app.workflows.state import ReviewGraphState

logger = logging.getLogger(__name__)


class WorkflowService:
    """Manages LangGraph workflow execution, checkpointing, and thread resumption."""

    def __init__(self, checkpointer: Any | None = None) -> None:
        self.checkpointer = checkpointer or MemorySaver()
        self.workflow = create_review_workflow(checkpointer=self.checkpointer)

    def _get_config(self, session_id: str | uuid.UUID) -> dict[str, Any]:
        """Generate thread configuration dictionary for LangGraph checkpointer."""
        return {"configurable": {"thread_id": str(session_id)}}

    async def _update_db_status(
        self,
        session_id: uuid.UUID,
        status: SessionStatus,
        error_message: str | None = None,
    ) -> None:
        """Update review session status in database."""
        async with async_session_factory() as db:
            stmt = select(ReviewSession).where(ReviewSession.id == session_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            if session:
                session.status = status
                if error_message:
                    session.error_message = error_message
                await db.commit()

    async def execute_initial_phase(
        self,
        session_id: uuid.UUID,
        initial_state: ReviewGraphState,
    ) -> None:
        """Run workflow from START until human_approval interrupt.

        Updates database status from CLASSIFYING to AWAITING_CHECKLIST_APPROVAL.
        """
        thread_id = str(session_id)
        config = self._get_config(thread_id)

        try:
            await self._update_db_status(session_id, SessionStatus.CLASSIFYING)
            # Run graph until interrupt
            await self.workflow.ainvoke(initial_state, config=config)
            await self._update_db_status(session_id, SessionStatus.AWAITING_CHECKLIST_APPROVAL)
        except Exception as exc:
            logger.error("Error during initial workflow execution for session %s: %s", session_id, exc)
            await self._update_db_status(session_id, SessionStatus.FAILED, error_message=str(exc))

    async def get_state_snapshot(self, session_id: uuid.UUID) -> dict[str, Any]:
        """Retrieve current checkpoint values for a session thread."""
        config = self._get_config(session_id)
        state_snapshot = await self.workflow.aget_state(config)
        return state_snapshot.values if state_snapshot else {}

    async def resume_with_approval(
        self,
        session_id: uuid.UUID,
        approved_checklist: list[dict[str, Any]],
    ) -> None:
        """Resume workflow execution from interrupt with approved checklist to completion."""
        config = self._get_config(session_id)

        try:
            await self._update_db_status(session_id, SessionStatus.REVIEWING)
            # Resume graph through review, consistency, and assessment
            final_state = await self.workflow.ainvoke(
                Command(resume=approved_checklist),
                config=config,
            )
            await self._update_db_status(session_id, SessionStatus.COMPLETED)
        except Exception as exc:
            logger.error("Error resuming workflow for session %s: %s", session_id, exc)
            await self._update_db_status(session_id, SessionStatus.FAILED, error_message=str(exc))

    async def answer_question(self, session_id: uuid.UUID, question: str) -> str:
        """Answer a question grounded in the completed review state."""
        state = await self.get_state_snapshot(session_id)
        if not state:
            return "Review state could not be located for this session."

        return await answer_grounded_question(state, question)


# Global workflow service singleton
workflow_service = WorkflowService()
