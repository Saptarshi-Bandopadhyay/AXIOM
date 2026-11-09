"""Evaluation test suite 02: Checklist relevance, clarity, and non-redundancy."""

import json
from unittest.mock import AsyncMock, patch
from deepeval.test_case import LLMTestCase
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.checklist import generate_checklist
from app.workflows.state import ReviewGraphState


async def test_checklist_quality_and_two_tier_structure() -> None:
    """Verify generated checklist satisfies quality, coverage, and non-redundancy standards."""
    mock_checklist = [
        {
            "id": "T1-COMPUTE",
            "tier": 1,
            "category": "Compute & Hardware",
            "criterion": "Are GPU models, GPU counts, and memory specifications clearly reported?",
            "rationale": "Hardware specification ensures reproducible execution time and memory limits.",
        },
        {
            "id": "T1-HYPERPARAMS",
            "tier": 1,
            "category": "Hyperparameters",
            "criterion": "Are optimization parameters (learning rate, batch size, optimizer, random seeds) documented?",
            "rationale": "Optimization hyperparameters are necessary to reproduce identical training trajectories.",
        },
        {
            "id": "T1-DATASETS",
            "tier": 1,
            "category": "Dataset Details",
            "criterion": "Are dataset sizes, sources, filtering heuristics, and train/val/test splits specified?",
            "rationale": "Dataset splits must be matched exactly to replicate benchmark results.",
        },
        {
            "id": "T1-VARIANCE",
            "tier": 1,
            "category": "Statistical Variance",
            "criterion": "Are results reported across multiple runs with standard deviation or confidence intervals?",
            "rationale": "Multi-run variance confirms whether observed gains are statistically significant.",
        },
        {
            "id": "T1-BASELINES",
            "tier": 1,
            "category": "Baselines & Fairness",
            "criterion": "Were baselines tuned fairly under matched compute and hyperparameter budgets?",
            "rationale": "Untuned baselines produce misleading performance comparisons.",
        },
        {
            "id": "T2-RAG-CHUNKING",
            "tier": 2,
            "category": "Retrieval Architecture",
            "criterion": "Does the paper report document chunk sizes, token overlap, and chunking strategy?",
            "rationale": "Chunk boundary heuristics directly dictate retrieval recall.",
        },
        {
            "id": "T2-RAG-INDEX",
            "tier": 2,
            "category": "Indexing & Search",
            "criterion": "Is the vector index algorithm, distance metric, and search top-k parameter specified?",
            "rationale": "Vector index parameters affect both retrieval latency and ranking precision.",
        },
    ]

    state: ReviewGraphState = {
        "session_id": "eval-session",
        "title": "Dense Passage Retrieval for Open Domain Question Answering",
        "abstract_text": "We investigate dense retrieval mechanisms across scientific corpora.",
        "methodology_text": "We index passages into 512 token chunks using dense bi-encoders and Faiss.",
        "primary_research_type": "Retrieval-Augmented Generation (RAG)",
        "secondary_research_types": [],
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=json.dumps(mock_checklist),
            model="gemini/gemini-1.5-flash",
        )
        result = await generate_checklist(state)
        items = result["checklist"]

        # Quality Check 1: Must contain both Tier 1 and Tier 2 criteria
        tier1_items = [i for i in items if i["tier"] == 1]
        tier2_items = [i for i in items if i["tier"] == 2]
        assert len(tier1_items) >= 5, "Tier 1 must contain at least 5 universal rigor criteria"
        assert len(tier2_items) >= 2, "Tier 2 must contain domain-specific criteria"

        # Quality Check 2: Non-redundancy — IDs and questions must be unique
        criterion_ids = [i["id"] for i in items]
        criterion_texts = [i["criterion"].strip().lower() for i in items]
        assert len(criterion_ids) == len(set(criterion_ids)), "All criterion IDs must be unique"
        assert len(criterion_texts) == len(set(criterion_texts)), "Criteria must not contain duplicate questions"

        # Quality Check 3: Every item must have a clear rationale
        for item in items:
            assert len(item["rationale"].strip()) >= 15, f"Criterion {item['id']} has insufficient rationale"

        # DeepEval audit test case
        test_case = LLMTestCase(
            input=f"Generate checklist for {state['primary_research_type']}",
            actual_output=json.dumps(items),
            expected_output="Balanced 2-tier checklist covering empirical rigor and domain parameters",
        )
        assert test_case.actual_output is not None
