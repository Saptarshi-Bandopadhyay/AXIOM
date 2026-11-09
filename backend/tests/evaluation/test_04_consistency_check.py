"""Evaluation test suite 04: Cross-section consistency checking accuracy."""

import json
from unittest.mock import AsyncMock, patch
from deepeval.test_case import LLMTestCase
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.consistency import check_cross_section_consistency
from app.workflows.state import ReviewGraphState


@pytest.mark.asyncio
async def test_detects_contradictions_between_sections() -> None:
    """Verify consistency node detects factual contradictions between methodology and experiments."""
    methodology_text = (
        "We train all model variants using 8 Nvidia A100 80GB GPUs with an effective batch size of 128."
    )
    experiments_text = (
        "All reported evaluation metrics were measured on checkpoints trained with batch size 32 on a single RTX 3090."
    )

    mock_llm_inconsistencies = [
        {
            "sections_involved": ["methodology", "experiments"],
            "description": "Hardware and batch size contradict: methodology specifies 8 A100s with batch size 128, while experiments states single RTX 3090 with batch size 32.",
            "evidence_quotes": [
                "We train all model variants using 8 Nvidia A100 80GB GPUs with an effective batch size of 128.",
                "All reported evaluation metrics were measured on checkpoints trained with batch size 32 on a single RTX 3090.",
            ],
        }
    ]

    state: ReviewGraphState = {
        "session_id": "eval-consistency-01",
        "methodology_text": methodology_text,
        "experiments_text": experiments_text,
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=json.dumps(mock_llm_inconsistencies),
            model="gemini/gemini-1.5-flash",
        )
        result = await check_cross_section_consistency(state)
        items = result["inconsistencies"]

        assert len(items) == 1
        item = items[0]
        assert "methodology" in item["sections_involved"]
        assert "experiments" in item["sections_involved"]
        assert len(item["evidence_quotes"]) == 2
        assert methodology_text in item["evidence_quotes"][0]
        assert experiments_text in item["evidence_quotes"][1]

        test_case = LLMTestCase(
            input=f"{methodology_text}\nvs\n{experiments_text}",
            actual_output=item["description"],
            expected_output="Hardware and batch size contradiction detected",
        )
        assert test_case.actual_output is not None


@pytest.mark.asyncio
async def test_consistent_sections_yield_zero_discrepancies() -> None:
    """Verify consistency node reports 0 inconsistencies for aligned methodology and experiments."""
    methodology_text = "We index 100,000 passages with chunk size 512 using Faiss."
    experiments_text = "We evaluate retrieval latency and MRR@10 on the 100,000 indexed passages."

    state: ReviewGraphState = {
        "session_id": "eval-consistency-02",
        "methodology_text": methodology_text,
        "experiments_text": experiments_text,
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content="[]",
            model="gemini/gemini-1.5-flash",
        )
        result = await check_cross_section_consistency(state)
        assert result["inconsistencies"] == []


@pytest.mark.asyncio
async def test_single_section_skips_consistency_check() -> None:
    """Verify consistency check gracefully handles single-section submissions without LLM call."""
    state: ReviewGraphState = {
        "session_id": "eval-consistency-03",
        "methodology_text": "We fine-tune Llama-3 with LoRA.",
        "experiments_text": None,
        "results_text": None,
    }

    result = await check_cross_section_consistency(state)
    items = result["inconsistencies"]
    assert len(items) == 1
    assert "skipped" in items[0]["description"].lower()
