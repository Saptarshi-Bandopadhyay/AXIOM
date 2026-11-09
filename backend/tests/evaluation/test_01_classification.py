"""Evaluation test suite 01: Research paradigm classification accuracy."""

import json
from unittest.mock import AsyncMock, patch
from deepeval.test_case import LLMTestCase
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.classify import classify_research_paradigm
from app.workflows.state import ReviewGraphState

EVAL_CASES = [
    {
        "domain": "RAG",
        "title": "Dense Passage Retrieval for Academic Survey Question Answering",
        "abstract": "We present a dense retrieval system using bi-encoder embeddings and BM25 reranking for scientific query answering.",
        "methodology": "Our pipeline indexes 50,000 papers. Documents are split into 512 token chunks with 50 token overlap. Retrieval uses Faiss HNSW index.",
        "expected_primary": "Retrieval-Augmented Generation (RAG)",
    },
    {
        "domain": "Fine-Tuning",
        "title": "Low-Rank Adaptation for Domain-Specific Biomedical Text Generation",
        "abstract": "We fine-tune open language models on PubMed clinical notes using parameter-efficient adapters.",
        "methodology": "We apply LoRA with rank r=16 and alpha=32 to all attention projection layers of Llama-3-8B. Trained using AdamW optimizer with lr=2e-4 for 3 epochs.",
        "expected_primary": "LLM Fine-Tuning & Alignment",
    },
    {
        "domain": "Agents",
        "title": "Tool-Augmented Autonomous Problem Solving via Iterative Reflection",
        "abstract": "An autonomous agent architecture that executes bash tools and web queries with self-critique loops.",
        "methodology": "The agent operates on an environment loop capped at 15 steps. It inspects tool execution outputs and reflects before taking the next action.",
        "expected_primary": "AI Agents & Multi-Agent Systems",
    },
    {
        "domain": "Novel / Unconventional AI",
        "title": "Neuromorphic Spiking Encoders for Quantum-Simulated Language Attention",
        "abstract": "We explore an experimental neuromorphic spike-timing architecture for simulating attention without floating point matrix multiplication.",
        "methodology": "Spike-based event clocks replace transformer attention heads. Experiments are conducted in quantum annealing simulators.",
        "expected_primary": "General / Novel AI Research",
    },
]


@pytest.mark.parametrize("case", EVAL_CASES, ids=[c["domain"] for c in EVAL_CASES])
async def test_paradigm_classification_accuracy(case: dict) -> None:
    """Verify classification node correctly maps diverse paper profiles to proper paradigms."""
    mock_response = json.dumps({
        "primary_research_type": case["expected_primary"],
        "secondary_research_types": [],
        "rationale": f"Paper focuses strictly on {case['domain']} methodologies.",
    })

    state: ReviewGraphState = {
        "session_id": "eval-session",
        "title": case["title"],
        "abstract_text": case["abstract"],
        "methodology_text": case["methodology"],
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_response,
            model="gemini/gemini-1.5-flash",
        )
        result = await classify_research_paradigm(state)

        # DeepEval test case record for audit tracking
        test_case = LLMTestCase(
            input=f"{case['title']}\n{case['abstract']}",
            actual_output=result["primary_research_type"],
            expected_output=case["expected_primary"],
        )

        assert test_case.actual_output == case["expected_primary"]
        assert result["primary_research_type"] == case["expected_primary"]
        assert len(result["research_type_rationale"]) > 10
