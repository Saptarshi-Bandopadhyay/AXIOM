"""Cross-section inconsistency check node for LangGraph workflow."""

import json
import logging
import re
from typing import Any
from app.core.llm_gateway import llm_gateway
from app.workflows.prompts.consistency import (
    CONSISTENCY_SYSTEM_PROMPT,
    build_consistency_prompt,
)
from app.workflows.state import InconsistencyItem, ReviewGraphState

logger = logging.getLogger(__name__)


def _extract_json_list(text: str) -> list[dict[str, Any]]:
    """Parse JSON array from LLM response text."""
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", cleaned)
        if match:
            cleaned = match.group(1)
    return json.loads(cleaned)


async def check_cross_section_consistency(state: ReviewGraphState) -> dict[str, Any]:
    """Identify factual contradictions between Methodology, Experiments, and Results sections."""
    experiments = state.get("experiments_text")
    results = state.get("results_text")

    # If only methodology was submitted, cross-section comparison is not possible
    if not experiments and not results:
        logger.info("Skipping consistency check: only methodology section was provided.")
        return {
            "inconsistencies": [
                {
                    "sections_involved": ["methodology"],
                    "description": "Cross-section check skipped: paper was submitted with methodology only.",
                    "evidence_quotes": [],
                }
            ]
        }

    prompt = build_consistency_prompt(
        methodology=state.get("methodology_text", ""),
        experiments=experiments,
        results=results,
    )

    messages = [
        {"role": "system", "content": CONSISTENCY_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await llm_gateway.complete(
            messages=messages,
            span_name="workflow_check_consistency",
            temperature=0.0,
        )
        raw_items = _extract_json_list(response.content)

        validated_items: list[dict[str, Any]] = []
        for raw in raw_items:
            item = InconsistencyItem(
                sections_involved=raw.get("sections_involved", ["methodology", "experiments"]),
                description=raw.get("description", ""),
                evidence_quotes=raw.get("evidence_quotes", []),
            )
            validated_items.append(item.model_dump())

        return {"inconsistencies": validated_items}
    except Exception as exc:
        logger.error("Consistency check node failed: %s", exc)
        return {"inconsistencies": []}
