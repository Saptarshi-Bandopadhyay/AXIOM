"""Qualitative overall methodology assessment synthesis node."""

import json
import logging
import re
from typing import Any
from app.core.llm_gateway import llm_gateway
from app.workflows.prompts.assessment import (
    ASSESSMENT_SYSTEM_PROMPT,
    build_assessment_prompt,
)
from app.workflows.state import OverallAssessment, ReviewGraphState

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON object from LLM response text."""
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", cleaned)
        if match:
            cleaned = match.group(1)
    return json.loads(cleaned)


async def synthesize_overall_assessment(state: ReviewGraphState) -> dict[str, Any]:
    """Synthesize findings and inconsistencies into a qualitative overall assessment."""
    findings = state.get("findings", [])
    inconsistencies = state.get("inconsistencies", [])
    primary_paradigm = state.get("primary_research_type")

    prompt = build_assessment_prompt(
        findings=findings,
        inconsistencies=inconsistencies,
        primary_paradigm=primary_paradigm,
    )

    messages = [
        {"role": "system", "content": ASSESSMENT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await llm_gateway.complete(
            messages=messages,
            span_name="workflow_synthesize_assessment",
            temperature=0.0,
        )
        parsed = _extract_json(response.content)

        # Normalize label to allowed literal
        raw_label = parsed.get("label", "Partially documented")
        allowed_labels = ["Well documented", "Partially documented", "Insufficiently documented"]
        label = raw_label if raw_label in allowed_labels else "Partially documented"

        assessment = OverallAssessment(
            label=label,
            summary=parsed.get("summary", ""),
            strengths=parsed.get("strengths", []),
            critical_gaps=parsed.get("critical_gaps", []),
        )

        return {"overall_assessment": assessment.model_dump()}
    except Exception as exc:
        logger.error("Assessment synthesis node failed: %s", exc)
        return {
            "overall_assessment": {
                "label": "Partially documented",
                "summary": f"Assessment synthesis fallback: {exc}",
                "strengths": [],
                "critical_gaps": [],
            }
        }
