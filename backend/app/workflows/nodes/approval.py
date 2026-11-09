"""Human-in-the-loop approval node using LangGraph interrupt()."""

import logging
from typing import Any
from langgraph.types import interrupt
from app.workflows.state import ReviewGraphState

logger = logging.getLogger(__name__)


def human_approval(state: ReviewGraphState) -> dict[str, Any]:
    """Pause workflow execution for human review and approval of the checklist.

    When resumed via Command(resume=...), updates the checklist with user edits
    and marks checklist_approved as True.
    """
    if state.get("checklist_approved"):
        return {"checklist_approved": True}

    logger.info("Pausing workflow at human_approval node via interrupt()...")

    # Interrupt execution and surface checklist to caller / UI
    resumed_data = interrupt({
        "message": "Please review, edit, and approve the methodology checklist.",
        "checklist": state.get("checklist", []),
    })

    # If the user supplied an edited or confirmed list on resume, save it
    if isinstance(resumed_data, list):
        return {
            "checklist": resumed_data,
            "checklist_approved": True,
        }

    if isinstance(resumed_data, dict) and "checklist" in resumed_data:
        return {
            "checklist": resumed_data["checklist"],
            "checklist_approved": True,
        }

    return {"checklist_approved": True}
