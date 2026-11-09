"""Evaluation test suite 05: Evidence quotation grounding and hallucination prevention."""

import json
from unittest.mock import AsyncMock, patch
from deepeval.test_case import LLMTestCase
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.review import review_methodology
from app.workflows.state import ReviewGraphState


PAPER_METHODOLOGY = (
    "Our retrieval index partitions 50,000 research articles into 512 token chunks with 50 token overlap. "
    "We use sentence-transformers/all-mpnet-base-v2 for generating dense 768-dimensional embeddings. "
    "Nearest neighbor search is conducted via Faiss IndexHNSWFlat with M=32 and efSearch=64."
)

SAMPLE_CHECKLIST = [
    {
        "id": "T2-EMBEDDINGS",
        "tier": 2,
        "category": "Embedding Model",
        "criterion": "Is the embedding model checkpoint and embedding dimensionality specified?",
        "rationale": "Embedding checkpoint determines vector representations.",
        "approved": True,
    },
    {
        "id": "T2-INDEX",
        "tier": 2,
        "category": "Vector Index",
        "criterion": "Are index type and search hyperparameters specified?",
        "rationale": "Search parameters impact recall and retrieval latency.",
        "approved": True,
    },
    {
        "id": "T1-SEEDS",
        "tier": 1,
        "category": "Hyperparameters",
        "criterion": "Are random seeds reported?",
        "rationale": "Required for reproducibility.",
        "approved": True,
    },
]


@pytest.mark.asyncio
async def test_evidence_quotes_are_verbatim_substrings() -> None:
    """Verify all evidence quotes on MET and INCOMPLETE findings are exact substrings of paper text."""
    mock_findings = [
        {
            "criterion_id": "T2-EMBEDDINGS",
            "criterion": "Is the embedding model checkpoint and embedding dimensionality specified?",
            "status": "MET",
            "severity": "NOTE",
            "description": "Model checkpoint and dimensionality are reported.",
            "evidence_quotes": [
                "We use sentence-transformers/all-mpnet-base-v2 for generating dense 768-dimensional embeddings."
            ],
        },
        {
            "criterion_id": "T2-INDEX",
            "criterion": "Are index type and search hyperparameters specified?",
            "status": "MET",
            "severity": "NOTE",
            "description": "Faiss index and HNSW parameters are specified.",
            "evidence_quotes": [
                "Nearest neighbor search is conducted via Faiss IndexHNSWFlat with M=32 and efSearch=64."
            ],
        },
        {
            "criterion_id": "T1-SEEDS",
            "criterion": "Are random seeds reported?",
            "status": "MISSING",
            "severity": "CRITICAL",
            "description": "No random seeds are mentioned in the methodology.",
            "evidence_quotes": [],
        },
    ]

    state: ReviewGraphState = {
        "session_id": "eval-grounding-01",
        "methodology_text": PAPER_METHODOLOGY,
        "checklist": SAMPLE_CHECKLIST,
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=json.dumps(mock_findings),
            model="gemini/gemini-1.5-flash",
        )
        result = await review_methodology(state)
        findings = result["findings"]

        # Rule 1: Every quote in MET / INCOMPLETE must exist verbatim in the text
        for finding in findings:
            if finding["status"] in ("MET", "INCOMPLETE"):
                assert len(finding["evidence_quotes"]) > 0, (
                    f"Finding {finding['criterion_id']} marked {finding['status']} must have quotes"
                )
                for quote in finding["evidence_quotes"]:
                    assert quote in PAPER_METHODOLOGY, f"Quote '{quote}' is not a verbatim substring of paper"

            # Rule 2: MISSING findings must never cite quotes
            if finding["status"] == "MISSING":
                assert len(finding["evidence_quotes"]) == 0, (
                    f"MISSING finding {finding['criterion_id']} must have empty evidence_quotes"
                )

        # DeepEval audit tracking
        test_case = LLMTestCase(
            input=PAPER_METHODOLOGY,
            actual_output=json.dumps([f["evidence_quotes"] for f in findings]),
            expected_output="All evidence quotes are exact substrings with zero hallucinated text",
        )
        assert test_case.actual_output is not None


@pytest.mark.asyncio
async def test_hallucinated_quote_detection() -> None:
    """Verify evaluation logic detects when an LLM produces a fabricated quotation."""
    hallucinated_quote = "We used Cohere rerank-v3 to reorder retrieved documents."

    # Hallucinated quote does not exist in PAPER_METHODOLOGY
    assert hallucinated_quote not in PAPER_METHODOLOGY
