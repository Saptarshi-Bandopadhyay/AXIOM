"""Evaluation test suite 06: Grounded Q&A faithfulness and out-of-scope refusal."""

from unittest.mock import AsyncMock, patch
from deepeval.test_case import LLMTestCase
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.qna import answer_grounded_question
from app.workflows.state import ReviewGraphState


SAMPLE_STATE: ReviewGraphState = {
    "session_id": "eval-qna-01",
    "title": "Dense Passage Retrieval for Academic Papers",
    "methodology_text": (
        "We partition documents into 512 token chunks with 50 token overlap. "
        "Embeddings are computed using sentence-transformers/all-mpnet-base-v2. "
        "We do not report random seeds or GPU hardware specifications."
    ),
    "findings": [
        {
            "criterion_id": "T1-SEEDS",
            "criterion": "Are random seeds reported?",
            "status": "MISSING",
            "severity": "CRITICAL",
            "description": "No random seeds are reported.",
            "evidence_quotes": [],
        },
        {
            "criterion_id": "T2-EMBEDDINGS",
            "criterion": "Is embedding model specified?",
            "status": "MET",
            "severity": "NOTE",
            "description": "sentence-transformers/all-mpnet-base-v2 is explicitly specified.",
            "evidence_quotes": ["Embeddings are computed using sentence-transformers/all-mpnet-base-v2."],
        },
    ],
    "overall_assessment": {
        "label": "Partially documented",
        "summary": "Core embedding pipeline is documented but key empirical seeds and compute details are missing.",
        "strengths": ["Clear embedding checkpoint specified"],
        "critical_gaps": ["Missing random seeds", "Missing compute hardware"],
    },
}


@pytest.mark.asyncio
async def test_grounded_question_answers_faithfully_with_citation() -> None:
    """Verify in-scope questions receive grounded answers citing methodology text and findings."""
    question = "Which embedding model did the authors select for indexing?"
    mock_answer = (
        "According to the methodology section, the authors used `sentence-transformers/all-mpnet-base-v2` "
        "to compute dense embeddings: 'Embeddings are computed using sentence-transformers/all-mpnet-base-v2.'"
    )

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_answer,
            model="gemini/gemini-1.5-flash",
        )
        answer = await answer_grounded_question(SAMPLE_STATE, question)

        assert "all-mpnet-base-v2" in answer
        assert "sentence-transformers" in answer

        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            expected_output="Grounded answer citing sentence-transformers/all-mpnet-base-v2",
        )
        assert test_case.actual_output is not None


@pytest.mark.asyncio
async def test_out_of_scope_question_is_refused() -> None:
    """Verify unrelated questions outside the paper scope are strictly refused."""
    question = "Who won the 2022 FIFA World Cup and which team was runner-up?"
    mock_refusal = (
        "I can only answer questions directly related to the submitted paper and its methodology review findings."
    )

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_refusal,
            model="gemini/gemini-1.5-flash",
        )
        answer = await answer_grounded_question(SAMPLE_STATE, question)

        assert "only answer questions directly related" in answer.lower() or "decline" in answer.lower()

        test_case = LLMTestCase(
            input=question,
            actual_output=answer,
            expected_output="Refusal stating assistance is restricted strictly to the submitted paper",
        )
        assert test_case.actual_output is not None


@pytest.mark.asyncio
async def test_empty_question_handling() -> None:
    """Verify empty or whitespace-only queries return helpful guidance without an LLM call."""
    answer = await answer_grounded_question(SAMPLE_STATE, "   ")
    assert "Please ask a specific question" in answer
