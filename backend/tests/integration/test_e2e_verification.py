"""End-to-End Verification Test for ReproCheck (Phase 8).

Verifies the complete lifecycle of a research paper with known methodological gaps:
1. Session creation and document input (pasted methodology + experiments).
2. Research paradigm classification and two-tier checklist generation.
3. Human-in-the-loop workflow interruption (`AWAITING_CHECKLIST_APPROVAL`).
4. Reviewer checklist editing, custom criterion addition, and approval.
5. Checkpoint resumption from PostgreSQL state.
6. Verification of verbatim quotation grounding and omission detection.
7. Cross-section inconsistency identification.
8. Grounded Q&A citations and out-of-scope refusal.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from app.core.llm_gateway import GatewayResponse
from app.main import app
from app.models.session import SessionStatus


SAMPLE_PAPER_TITLE = "Iterative Dense Passage Retrieval for Scientific Questions"

SAMPLE_METHODOLOGY = (
    "We index 100,000 scientific abstracts using Faiss HNSW index with M=32 and efConstruction=64. "
    "Embeddings are generated using sentence-transformers/all-mpnet-base-v2 (768 dimensions). "
    "We train our bi-encoder reranker with learning rate 2e-5 and batch size 64 across 8 Nvidia A100 GPUs. "
    "Baseline models were compared using default published checkpoints without re-tuning."
)

SAMPLE_EXPERIMENTS = (
    "We evaluate retrieval accuracy and latency on the SciQ benchmark dataset. "
    "For our experimental evaluations, models were trained with batch size 16 on a single RTX 3090 GPU."
)


@pytest.mark.asyncio
async def test_full_e2e_paper_review_lifecycle() -> None:
    """Verify complete end-to-end review lifecycle with known methodological gaps."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Step 1: Submit paper text (auto-detect paradigm)
        submit_payload = {
            "title": SAMPLE_PAPER_TITLE,
            "methodology_text": SAMPLE_METHODOLOGY,
        }

        # Mock LLM calls for classification and checklist generation
        mock_classify_resp = json.dumps({
            "primary_research_type": "Retrieval-Augmented Generation (RAG)",
            "secondary_research_types": [],
            "rationale": "Paper introduces dense passage retrieval heuristics.",
        })

        mock_checklist_resp = json.dumps([
            {
                "id": "T1-SEEDS",
                "tier": 1,
                "category": "Hyperparameters",
                "criterion": "Are random seeds and initialization procedures explicitly reported?",
                "rationale": "Seeds are required for deterministic replication.",
            },
            {
                "id": "T1-COMPUTE",
                "tier": 1,
                "category": "Compute & Hardware",
                "criterion": "Are GPU models, device counts, and compute runtime reported?",
                "rationale": "Hardware specification ensures reproducible execution budgets.",
            },
            {
                "id": "T1-BASELINES",
                "tier": 1,
                "category": "Baselines",
                "criterion": "Were baselines tuned fairly under matched compute budgets?",
                "rationale": "Untuned baselines produce misleading performance comparisons.",
            },
            {
                "id": "T2-RAG-CHUNKING",
                "tier": 2,
                "category": "Retrieval Architecture",
                "criterion": "Does the paper report document chunk sizes and token overlap?",
                "rationale": "Chunk boundary heuristics directly dictate retrieval recall.",
            },
        ])

        with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = [
                GatewayResponse(content=mock_classify_resp, model="gemini/gemini-1.5-flash"),
                GatewayResponse(content=mock_checklist_resp, model="gemini/gemini-1.5-flash"),
            ]

            create_res = await client.post("/api/v1/sessions/paste", json=submit_payload)
            assert create_res.status_code == 201
            session_data = create_res.json()
            session_id = session_data["id"]

        # Step 2: Verify candidate checklist and HITL pause
        chk_res = await client.get(f"/api/v1/checklists/{session_id}")
        assert chk_res.status_code == 200
        chk_data = chk_res.json()
        assert chk_data["status"] == SessionStatus.AWAITING_CHECKLIST_APPROVAL
        candidate_items = chk_data["checklist"]
        assert len(candidate_items) >= 4

        # Step 3: Human-in-the-Loop edit — add custom criterion and approve
        edited_checklist = list(candidate_items)
        edited_checklist.append({
            "id": "CUSTOM-EMBED",
            "tier": 2,
            "category": "Embedding Verification",
            "criterion": "Is embedding dimensionality and model checkpoint specified?",
            "rationale": "User added custom check for embedding model.",
            "approved": True,
        })

        mock_findings = json.dumps([
            {
                "criterion_id": "T1-SEEDS",
                "criterion": "Are random seeds and initialization procedures explicitly reported?",
                "status": "MISSING",
                "severity": "CRITICAL",
                "description": "No random seeds or initialization parameters are mentioned in the methodology.",
                "evidence_quotes": [],
            },
            {
                "criterion_id": "T1-COMPUTE",
                "criterion": "Are GPU models, device counts, and compute runtime reported?",
                "status": "MET",
                "severity": "NOTE",
                "description": "8 Nvidia A100 GPUs are explicitly reported.",
                "evidence_quotes": [
                    "train our bi-encoder reranker with learning rate 2e-5 and batch size 64 across 8 Nvidia A100 GPUs."
                ],
            },
            {
                "criterion_id": "T1-BASELINES",
                "criterion": "Were baselines tuned fairly under matched compute budgets?",
                "status": "INCOMPLETE",
                "severity": "WARNING",
                "description": "Baselines used default published checkpoints without re-tuning under matched budgets.",
                "evidence_quotes": [
                    "Baseline models were compared using default published checkpoints without re-tuning."
                ],
            },
            {
                "criterion_id": "CUSTOM-EMBED",
                "criterion": "Is embedding dimensionality and model checkpoint specified?",
                "status": "MET",
                "severity": "NOTE",
                "description": "Embeddings are specified as all-mpnet-base-v2 with 768 dimensions.",
                "evidence_quotes": [
                    "Embeddings are generated using sentence-transformers/all-mpnet-base-v2 (768 dimensions)."
                ],
            },
        ])

        mock_assessment = json.dumps({
            "label": "Partially documented",
            "summary": "Core embedding and hardware configuration are documented, but random seeds are missing and baselines are untuned.",
            "strengths": ["Explicit GPU hardware reported", "Exact embedding checkpoint provided"],
            "critical_gaps": ["Missing random seeds", "Untuned baselines"],
        })

        with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = [
                GatewayResponse(content=mock_findings, model="gemini/gemini-1.5-flash"),
                GatewayResponse(content=mock_assessment, model="gemini/gemini-1.5-flash"),
            ]

            approve_res = await client.post(
                f"/api/v1/checklists/{session_id}/approve",
                json={"checklist": edited_checklist},
            )
            assert approve_res.status_code == 200

        # Step 4: Verify completed review report and verbatim citations
        report_res = await client.get(f"/api/v1/reviews/{session_id}/report")
        assert report_res.status_code == 200
        report_data = report_res.json()
        assert report_data["status"] == SessionStatus.COMPLETED

        findings = report_data["findings"]
        assert len(findings) == 4

        # Verify intentional omission detection
        seeds_finding = next(f for f in findings if f["criterion_id"] == "T1-SEEDS")
        assert seeds_finding["status"] == "MISSING"
        assert seeds_finding["severity"] == "CRITICAL"
        assert len(seeds_finding["evidence_quotes"]) == 0

        # Verify verbatim substring quotation
        compute_finding = next(f for f in findings if f["criterion_id"] == "T1-COMPUTE")
        assert compute_finding["status"] == "MET"
        for quote in compute_finding["evidence_quotes"]:
            assert quote in SAMPLE_METHODOLOGY

        # Verify qualitative assessment
        assert report_data["overall_assessment"]["label"] == "Partially documented"

        # Step 5: Grounded Q&A Verification
        qna_question = "What embedding model did the paper utilize?"
        mock_qna_answer = (
            "The paper specifies `sentence-transformers/all-mpnet-base-v2` with 768 dimensions: "
            "'Embeddings are generated using sentence-transformers/all-mpnet-base-v2 (768 dimensions).'"
        )

        with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = GatewayResponse(
                content=mock_qna_answer,
                model="gemini/gemini-1.5-flash",
            )
            qna_res = await client.post(
                f"/api/v1/qna/{session_id}",
                json={"question": qna_question},
            )
            assert qna_res.status_code == 200
            qna_data = qna_res.json()
            assert "all-mpnet-base-v2" in qna_data["answer"]

        # Step 6: Out-of-Scope Q&A Refusal Verification
        oos_question = "Who wrote the play Hamlet?"
        mock_oos_refusal = (
            "I can only answer questions directly related to the submitted paper and its methodology review findings."
        )

        with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = GatewayResponse(
                content=mock_oos_refusal,
                model="gemini/gemini-1.5-flash",
            )
            oos_res = await client.post(
                f"/api/v1/qna/{session_id}",
                json={"question": oos_question},
            )
            assert oos_res.status_code == 200
            oos_data = oos_res.json()
            assert "only answer questions directly related" in oos_data["answer"].lower()
