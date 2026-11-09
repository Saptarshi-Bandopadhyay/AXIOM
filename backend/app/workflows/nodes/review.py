"""Methodology completeness review node for LangGraph workflow."""

import json
import logging
import re
from typing import Any
from app.core.llm_gateway import llm_gateway
from app.workflows.prompts.review import (
    REVIEW_SYSTEM_PROMPT,
    build_review_prompt,
)
from app.workflows.state import ReviewFinding, ReviewGraphState

logger = logging.getLogger(__name__)


def _extract_json_list(text: str) -> list[dict[str, Any]]:
    """Parse JSON array from LLM response text."""
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", cleaned)
        if match:
            cleaned = match.group(1)
    return json.loads(cleaned)


async def review_methodology(state: ReviewGraphState) -> dict[str, Any]:
    """Evaluate submitted methodology against approved checklist criteria."""
    checklist = [item for item in state.get("checklist", []) if item.get("approved", True)]
    if not checklist:
        logger.warning("No approved checklist items found for review.")
        return {"findings": []}

    prompt = build_review_prompt(
        checklist=checklist,
        methodology=state.get("methodology_text", ""),
        experiments=state.get("experiments_text"),
    )

    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await llm_gateway.complete(
            messages=messages,
            span_name="workflow_review_methodology",
            temperature=0.0,
        )
        raw_findings = _extract_json_list(response.content)

        # Validate with Pydantic ReviewFinding schema
        validated_findings: list[dict[str, Any]] = []
        for raw in raw_findings:
            finding = ReviewFinding(
                criterion_id=raw.get("criterion_id", "CRIT"),
                criterion=raw.get("criterion", ""),
                status=raw.get("status", "INCOMPLETE"),
                severity=raw.get("severity", "WARNING"),
                description=raw.get("description", ""),
                evidence_quotes=raw.get("evidence_quotes", []),
            )
            validated_findings.append(finding.model_dump())

        return {"findings": validated_findings}
    except Exception as exc:
        logger.error("Methodology review node failed: %s", exc)
        return {
            "findings": [
                {
                    "criterion_id": "ERROR",
                    "criterion": "Review Execution",
                    "status": "INCOMPLETE",
                    "severity": "CRITICAL",
                    "description": f"Automated review failed to complete: {exc}",
                    "evidence_quotes": [],
                }
            ]
        }
