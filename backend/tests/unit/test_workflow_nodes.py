"""Unit tests for individual LangGraph workflow nodes."""

import json
from unittest.mock import AsyncMock, patch
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.assessment import synthesize_overall_assessment
from app.workflows.nodes.checklist import generate_checklist
from app.workflows.nodes.classify import classify_research_paradigm
from app.workflows.nodes.consistency import check_cross_section_consistency
from app.workflows.nodes.qna import answer_grounded_question
from app.workflows.nodes.review import review_methodology
from app.workflows.state import ReviewGraphState


@pytest.fixture
def base_state() -> ReviewGraphState:
    """Fixture providing baseline review state."""
    return {
        "session_id": "test-session",
        "title": "Dense Retrieval for Academic Methodology Review",
        "abstract_text": "We present an evaluation framework for RAG methodology.",
        "methodology_text": "Our system uses BM25 and bi-encoders with chunk size 512. Hardware: 4x NVIDIA A100 GPUs.",
        "experiments_text": "We evaluate on 50 arXiv papers with 5 random seeds.",
        "results_text": "Achieves 92.4% precision on citation grounding.",
        "input_type": "PDF_UPLOAD",
        "checklist": [],
        "findings": [],
        "inconsistencies": [],
    }


async def test_classify_node_automatic(base_state: ReviewGraphState) -> None:
    """Verify automatic classification node parses LLM response correctly."""
    mock_llm_json = json.dumps({
        "primary_research_type": "Retrieval-Augmented Generation (RAG)",
        "secondary_research_types": ["AI System Evaluation & Benchmarking"],
        "rationale": "Focuses on chunking, dense retrieval, and citation verification.",
    })

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_llm_json, model="gemini/gemini-1.5-flash"
        )
        result = await classify_research_paradigm(base_state)

        assert result["primary_research_type"] == "Retrieval-Augmented Generation (RAG)"
        assert "AI System Evaluation & Benchmarking" in result["secondary_research_types"]
        assert "dense retrieval" in result["research_type_rationale"]


async def test_classify_node_respects_user_preselection(base_state: ReviewGraphState) -> None:
    """Verify classification node preserves user-selected primary research paradigm."""
    base_state["primary_research_type"] = "AI Agents & Multi-Agent Systems"

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        result = await classify_research_paradigm(base_state)

        assert result["primary_research_type"] == "AI Agents & Multi-Agent Systems"
        mock_complete.assert_not_called()


async def test_generate_checklist_node(base_state: ReviewGraphState) -> None:
    """Verify checklist generation creates Tier 1 and Tier 2 criteria."""
    base_state["primary_research_type"] = "Retrieval-Augmented Generation (RAG)"

    mock_checklist_json = json.dumps([
        {
            "id": "T1-COMPUTE",
            "tier": 1,
            "category": "Compute & Hardware",
            "criterion": "Are GPU models and counts reported?",
            "rationale": "Verifies compute feasibility.",
        },
        {
            "id": "T2-RAG-CHUNKING",
            "tier": 2,
            "category": "RAG Configuration",
            "criterion": "Is chunk size and overlap specified?",
            "rationale": "Chunking is critical to retriever performance.",
        },
    ])

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_checklist_json, model="gemini/gemini-1.5-flash"
        )
        result = await generate_checklist(base_state)

        items = result["checklist"]
        assert len(items) == 2
        assert items[0]["id"] == "T1-COMPUTE"
        assert items[0]["tier"] == 1
        assert items[0]["approved"] is True
        assert items[1]["id"] == "T2-RAG-CHUNKING"
        assert items[1]["tier"] == 2


async def test_review_methodology_node(base_state: ReviewGraphState) -> None:
    """Verify methodology review produces validated ReviewFinding items with quotes."""
    base_state["checklist"] = [
        {
            "id": "T1-COMPUTE",
            "tier": 1,
            "category": "Compute & Hardware",
            "criterion": "Are GPU models reported?",
            "approved": True,
        }
    ]

    mock_findings_json = json.dumps([
        {
            "criterion_id": "T1-COMPUTE",
            "criterion": "Are GPU models reported?",
            "status": "MET",
            "severity": "NOTE",
            "description": "The paper explicitly specifies 4x NVIDIA A100 GPUs.",
            "evidence_quotes": ["Hardware: 4x NVIDIA A100 GPUs."],
        }
    ])

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_findings_json, model="gemini/gemini-1.5-flash"
        )
        result = await review_methodology(base_state)

        findings = result["findings"]
        assert len(findings) == 1
        assert findings[0]["status"] == "MET"
        assert "4x NVIDIA A100 GPUs" in findings[0]["evidence_quotes"][0]


async def test_consistency_node_skips_when_only_methodology(base_state: ReviewGraphState) -> None:
    """Verify consistency node skips when only methodology text is available."""
    base_state["experiments_text"] = None
    base_state["results_text"] = None

    result = await check_cross_section_consistency(base_state)
    assert len(result["inconsistencies"]) == 1
    assert "skipped" in result["inconsistencies"][0]["description"]


async def test_consistency_node_identifies_discrepancy(base_state: ReviewGraphState) -> None:
    """Verify consistency node reports discrepancies between sections."""
    mock_inconsistencies_json = json.dumps([
        {
            "sections_involved": ["methodology", "experiments"],
            "description": "Methodology specifies 512 token chunks, but experiments note 1024 chunks.",
            "evidence_quotes": ["chunk size 512", "chunk size 1024"],
        }
    ])

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_inconsistencies_json, model="gemini/gemini-1.5-flash"
        )
        result = await check_cross_section_consistency(base_state)

        assert len(result["inconsistencies"]) == 1
        assert "Methodology specifies 512" in result["inconsistencies"][0]["description"]


async def test_synthesize_assessment_node(base_state: ReviewGraphState) -> None:
    """Verify assessment node assigns qualitative label without numerical scores."""
    base_state["findings"] = [
        {
            "criterion_id": "T1-COMPUTE",
            "criterion": "Compute reported",
            "status": "MET",
            "severity": "NOTE",
            "description": "Hardware reported clearly.",
            "evidence_quotes": [],
        }
    ]

    mock_assessment_json = json.dumps({
        "label": "Well documented",
        "summary": "Methodology is thoroughly detailed with clear empirical specifications.",
        "strengths": ["Hardware specifications provided", "Dataset details clear"],
        "critical_gaps": [],
    })

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=mock_assessment_json, model="gemini/gemini-1.5-flash"
        )
        result = await synthesize_overall_assessment(base_state)

        assessment = result["overall_assessment"]
        assert assessment["label"] == "Well documented"
        assert len(assessment["strengths"]) == 2
        assert assessment["critical_gaps"] == []


async def test_qna_node_grounded_response(base_state: ReviewGraphState) -> None:
    """Verify grounded Q&A returns cited paper answers and out-of-scope refusals."""
    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content="The paper reports using 4x NVIDIA A100 GPUs with chunk size 512.",
            model="gemini/gemini-1.5-flash",
        )
        answer = await answer_grounded_question(base_state, "What hardware was used?")
        assert "4x NVIDIA A100" in answer
