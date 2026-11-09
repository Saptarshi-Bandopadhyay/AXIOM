"""Grounded question answering node restricted to paper text and review findings."""

import logging
from typing import Any
from app.core.llm_gateway import llm_gateway
from app.workflows.prompts.qna import (
    QNA_SYSTEM_PROMPT,
    build_qna_prompt,
)
from app.workflows.state import ReviewGraphState

logger = logging.getLogger(__name__)


async def answer_grounded_question(
    state: ReviewGraphState,
    question: str,
) -> str:
    """Answer a user question strictly based on the submitted paper and review findings.

    Args:
        state: Completed or current workflow graph state.
        question: User inquiry text.

    Returns:
        str: Grounded response text with evidence citations or explicit refusal if out-of-scope.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        return "Please ask a specific question regarding the submitted paper or review findings."

    prompt = build_qna_prompt(
        question=cleaned_question,
        methodology=state.get("methodology_text", ""),
        experiments=state.get("experiments_text"),
        results=state.get("results_text"),
        findings=state.get("findings", []),
        assessment=state.get("overall_assessment"),
    )

    messages = [
        {"role": "system", "content": QNA_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await llm_gateway.complete(
            messages=messages,
            span_name="workflow_grounded_qna",
            temperature=0.0,
        )
        return response.content.strip()
    except Exception as exc:
        logger.error("Grounded Q&A node failed: %s", exc)
        return f"Unable to answer question at this time due to an error: {exc}"
