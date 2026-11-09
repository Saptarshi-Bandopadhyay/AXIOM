"""Integration tests for the LangGraph review workflow engine."""

import json
from unittest.mock import AsyncMock, patch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.graph import create_review_workflow
from app.workflows.nodes.qna import answer_grounded_question
from app.workflows.state import ReviewGraphState


@pytest.fixture
def mock_llm_responses() -> dict[str, str]:
    """Provide realistic JSON responses for workflow nodes."""
    return {
        "classify": json.dumps({
            "primary_research_type": "Retrieval-Augmented Generation (RAG)",
            "secondary_research_types": ["LLM Fine-Tuning & Alignment"],
            "rationale": "Introduces adaptive retrieval thresholds and reflection tokens during generation.",
        }),
        "checklist": json.dumps([
            {
                "id": "T1-COMPUTE",
                "tier": 1,
                "category": "Compute & Hardware",
                "criterion": "Are GPU models and counts reported?",
                "rationale": "Verifies compute reproducibility.",
            },
            {
                "id": "T1-HYPERPARAMS",
                "tier": 1,
                "category": "Hyperparameters",
                "criterion": "Are learning rate, optimizer, and seed reported?",
                "rationale": "Required to replicate training dynamics.",
            },
            {
                "id": "T2-RAG-CHUNKING",
                "tier": 2,
                "category": "RAG Configuration",
                "criterion": "Is retriever chunk size and threshold documented?",
                "rationale": "Essential for retrieval accuracy.",
            },
        ]),
        "review": json.dumps([
            {
                "criterion_id": "T1-COMPUTE",
                "criterion": "Are GPU models and counts reported?",
                "status": "MET",
                "severity": "NOTE",
                "description": "Hardware is documented as 8x NVIDIA A100 GPUs in the experiments section.",
                "evidence_quotes": ["Evaluated on PopQA and PubHealth using 8x NVIDIA A100 GPUs."],
            },
            {
                "criterion_id": "T1-HYPERPARAMS",
                "criterion": "Are learning rate, optimizer, and seed reported?",
                "status": "INCOMPLETE",
                "severity": "WARNING",
                "description": "LoRA rank 16 and AdamW are reported, but learning rate value and random seeds are omitted.",
                "evidence_quotes": ["fine-tuned on Llama-2-7B using LoRA rank 16 with AdamW optimizer."],
            },
            {
                "criterion_id": "T2-RAG-CHUNKING",
                "criterion": "Is retriever chunk size and threshold documented?",
                "status": "MET",
                "severity": "NOTE",
                "description": "Retrieve threshold 0.5 and chunk size 512 tokens are clearly reported.",
                "evidence_quotes": ["Retrieve threshold is 0.5. Chunk size is 512 tokens."],
            },
        ]),
        "consistency": json.dumps([]),
        "assessment": json.dumps({
            "label": "Partially documented",
            "summary": "Core model parameters and compute are reported, but exact learning rates and seeds are omitted.",
            "strengths": ["Clear hardware specification (8x A100)", "Retriever chunk size and threshold documented"],
            "critical_gaps": ["Missing learning rate and random seed variance"],
        }),
    }


async def test_full_review_workflow_lifecycle_with_human_in_the_loop(
    mock_llm_responses: dict[str, str],
) -> None:
    """Verify end-to-end workflow execution:

    1. START -> classify -> generate_checklist.
    2. Pauses at human_approval via interrupt().
    3. Resumes via Command(resume=approved_checklist).
    4. Executes review -> consistency -> assessment -> END.
    5. Answers grounded Q&A queries.
    """
    checkpointer = MemorySaver()
    workflow = create_review_workflow(checkpointer=checkpointer)

    thread_id = "test-session-thread-101"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: ReviewGraphState = {
        "session_id": thread_id,
        "title": "Self-RAG: Learning to Retrieve, Generate, and Critique",
        "abstract_text": "We introduce Self-RAG, an adaptive retrieval-augmented framework.",
        "methodology_text": (
            "Our model is fine-tuned on Llama-2-7B using LoRA rank 16 with AdamW optimizer. "
            "Retrieve threshold is 0.5. Chunk size is 512 tokens."
        ),
        "experiments_text": "Evaluated on PopQA and PubHealth using 8x NVIDIA A100 GPUs.",
        "results_text": "Self-RAG achieves 54.9% accuracy on PopQA.",
        "input_type": "PDF_UPLOAD",
    }

    # Helper simulating model gateway responses per workflow node span
    async def mock_gateway_complete(messages, span_name=None, **kwargs):
        if span_name == "workflow_classification":
            content = mock_llm_responses["classify"]
        elif span_name == "workflow_generate_checklist":
            content = mock_llm_responses["checklist"]
        elif span_name == "workflow_review_methodology":
            content = mock_llm_responses["review"]
        elif span_name == "workflow_check_consistency":
            content = mock_llm_responses["consistency"]
        elif span_name == "workflow_synthesize_assessment":
            content = mock_llm_responses["assessment"]
        else:
            content = "{}"
        return GatewayResponse(content=content, model="gemini/gemini-1.5-flash")

    with patch("app.core.llm_gateway.llm_gateway.complete", side_effect=mock_gateway_complete):
        # Step 1: Execute graph from START until interrupt
        await workflow.ainvoke(initial_state, config=config)

        # Step 2: Inspect checkpointed state at interrupt
        state_snapshot = await workflow.aget_state(config)
        assert state_snapshot.next == ("human_approval",)
        assert state_snapshot.values["primary_research_type"] == "Retrieval-Augmented Generation (RAG)"
        assert len(state_snapshot.values["checklist"]) == 3
        assert state_snapshot.values.get("checklist_approved") is not True

        # Step 3: Human reviews and confirms the checklist
        approved_checklist = list(state_snapshot.values["checklist"])
        # Add a custom criterion from user
        approved_checklist.append({
            "id": "USER-CUSTOM-1",
            "tier": 2,
            "category": "User Custom",
            "criterion": "Is the embedding model checkpoint specified?",
            "rationale": "User requested verification of embedding weights.",
            "approved": True,
        })

        # Step 4: Resume workflow from checkpoint with approved checklist
        final_state = await workflow.ainvoke(
            Command(resume=approved_checklist),
            config=config,
        )

        # Step 5: Verify execution completed successfully to END
        assert final_state["checklist_approved"] is True
        assert len(final_state["checklist"]) == 4

        # Verify review findings
        assert "findings" in final_state
        assert len(final_state["findings"]) >= 1
        assert any(f["criterion_id"] == "T1-COMPUTE" and f["status"] == "MET" for f in final_state["findings"])

        # Verify overall qualitative assessment
        assessment = final_state["overall_assessment"]
        assert assessment is not None
        assert assessment["label"] in ("Well documented", "Partially documented", "Insufficiently documented")
        assert len(assessment["strengths"]) >= 1

        # Step 6: Test grounded Q&A with final state
        with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_qna_complete:
            mock_qna_complete.return_value = GatewayResponse(
                content="The paper specifies using 8x NVIDIA A100 GPUs and chunk size of 512 tokens.",
                model="gemini/gemini-1.5-flash",
            )
            answer = await answer_grounded_question(final_state, "What hardware and chunk size were used?")
            assert "8x NVIDIA A100 GPUs" in answer
            assert "512 tokens" in answer
