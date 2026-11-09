"""Research paradigm classification node for LangGraph workflow."""

import json
import logging
import re
from typing import Any
from app.core.llm_gateway import llm_gateway
from app.workflows.prompts.classification import (
    CLASSIFICATION_SYSTEM_PROMPT,
    build_classification_prompt,
)
from app.workflows.state import ReviewGraphState

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON object from LLM response text."""
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned)
        if match:
            cleaned = match.group(1)
    return json.loads(cleaned)


async def classify_research_paradigm(state: ReviewGraphState) -> dict[str, Any]:
    """Classify the paper into primary and secondary research paradigms.

    Respects manual user selection if primary_research_type was already provided in state.
    """
    existing_primary = state.get("primary_research_type")
    if existing_primary:
        logger.info("Using pre-selected primary research type: %s", existing_primary)
        return {
            "primary_research_type": existing_primary,
            "secondary_research_types": state.get("secondary_research_types") or [],
            "research_type_rationale": "Selected by user prior to review.",
        }

    prompt = build_classification_prompt(
        title=state.get("title"),
        abstract=state.get("abstract_text"),
        methodology=state.get("methodology_text", ""),
    )

    messages = [
        {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await llm_gateway.complete(
            messages=messages,
            span_name="workflow_classification",
            temperature=0.0,
        )
        parsed = _extract_json(response.content)
        return {
            "primary_research_type": parsed.get("primary_research_type", "General / Novel AI Research"),
            "secondary_research_types": parsed.get("secondary_research_types", []),
            "research_type_rationale": parsed.get("rationale", ""),
        }
    except Exception as exc:
        logger.error("Classification node failed: %s", exc)
        # Safe fallback default
        return {
            "primary_research_type": "General / Novel AI Research",
            "secondary_research_types": [],
            "research_type_rationale": f"Automatic classification fallback due to error: {exc}",
        }
