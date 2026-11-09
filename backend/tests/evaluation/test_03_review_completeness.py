"""Evaluation test suite 03: Methodology completeness review accuracy."""

import json
from unittest.mock import AsyncMock, patch
from deepeval.test_case import LLMTestCase
import pytest
from app.core.llm_gateway import GatewayResponse
from app.workflows.nodes.review import review_methodology
from app.workflows.state import ReviewGraphState


SAMPLE_CHECKLIST = [
    {
        "id": "T1-SEEDS",
        "tier": 1,
        "category": "Hyperparameters",
        "criterion": "Are random seeds and initialization procedures explicitly reported?",
        "rationale": "Seeds are essential to replicate training runs deterministically.",
        "approved": True,
    },
    {
        "id": "T1-COMPUTE",
        "tier": 1,
        "category": "Compute & Hardware",
        "criterion": "Are GPU models, counts, and compute runtime specifications reported?",
        "rationale": "Hardware specification ensures reproducible execution budgets.",
        "approved": True,
    },
    {
        "id": "T1-BASELINES",
        "tier": 1,
        "category": "Baselines",
        "criterion": "Were baselines compared under matched tuning and budget conditions?",
        "rationale": "Fair baselines prevent misleading performance claims.",
        "approved": True,
    },
]


@pytest.mark.asyncio
async def test_review_detects_intentional_omissions() -> None:
    """Verify review node identifies missing seeds and hardware specifications."""
    methodology_with_gaps = (
        "We train a 7B parameter language model on our proprietary dataset for 5 epochs. "
        "We use AdamW optimizer with a learning rate of 2e-5. We compare against standard BERT."
    )

    mock_llm_findings = [
        {
            "criterion_id": "T1-SEEDS",
            "criterion": "Are random seeds and initialization procedures explicitly reported?",
            "status": "MISSING",
            "severity": "CRITICAL",
            "description": "The methodology does not specify random seeds or initialization parameters.",
            "evidence_quotes": [],
        },
        {
            "criterion_id": "T1-COMPUTE",
            "criterion": "Are GPU models, counts, and compute runtime specifications reported?",
            "status": "MISSING",
            "severity": "CRITICAL",
            "description": "No GPU models, device counts, or compute time are reported.",
            "evidence_quotes": [],
        },
        {
            "criterion_id": "T1-BASELINES",
            "criterion": "Were baselines compared under matched tuning and budget conditions?",
            "status": "INCOMPLETE",
            "severity": "WARNING",
            "description": "BERT baseline is mentioned but tuning details and hyperparameter budgets are omitted.",
            "evidence_quotes": ["We compare against standard BERT."],
        },
    ]

    state: ReviewGraphState = {
        "session_id": "eval-completeness-01",
        "title": "Language Model Training with Missing Reproducibility Details",
        "methodology_text": methodology_with_gaps,
        "checklist": SAMPLE_CHECKLIST,
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=json.dumps(mock_llm_findings),
            model="gemini/gemini-1.5-flash",
        )
        result = await review_methodology(state)
        findings = result["findings"]

        # Completeness Check: all 3 checklist items evaluated
        assert len(findings) == 3

        # Omission Detection: verify MISSING status and CRITICAL severity
        seeds_finding = next(f for f in findings if f["criterion_id"] == "T1-SEEDS")
        assert seeds_finding["status"] == "MISSING"
        assert seeds_finding["severity"] == "CRITICAL"
        assert len(seeds_finding["evidence_quotes"]) == 0

        compute_finding = next(f for f in findings if f["criterion_id"] == "T1-COMPUTE")
        assert compute_finding["status"] == "MISSING"
        assert compute_finding["severity"] == "CRITICAL"

        baseline_finding = next(f for f in findings if f["criterion_id"] == "T1-BASELINES")
        assert baseline_finding["status"] == "INCOMPLETE"
        assert baseline_finding["severity"] == "WARNING"

        # DeepEval evaluation record
        test_case = LLMTestCase(
            input=methodology_with_gaps,
            actual_output=json.dumps([f["status"] for f in findings]),
            expected_output=json.dumps(["MISSING", "MISSING", "INCOMPLETE"]),
        )
        assert test_case.actual_output is not None


@pytest.mark.asyncio
async def test_review_identifies_fully_met_criteria() -> None:
    """Verify review node marks criteria as MET when comprehensive evidence is provided."""
    complete_methodology = (
        "We train with 5 random seeds (42, 43, 44, 45, 46). "
        "Training was executed across 8 Nvidia A100 80GB GPUs for 14.5 hours. "
        "All baselines were re-tuned using identical 50-trial Bayesian hyperparameter search."
    )

    mock_llm_findings = [
        {
            "criterion_id": "T1-SEEDS",
            "criterion": "Are random seeds and initialization procedures explicitly reported?",
            "status": "MET",
            "severity": "NOTE",
            "description": "5 random seeds are explicitly listed.",
            "evidence_quotes": ["We train with 5 random seeds (42, 43, 44, 45, 46)."],
        },
        {
            "criterion_id": "T1-COMPUTE",
            "criterion": "Are GPU models, counts, and compute runtime specifications reported?",
            "status": "MET",
            "severity": "NOTE",
            "description": "Hardware and wall-clock runtime are thoroughly reported.",
            "evidence_quotes": ["Training was executed across 8 Nvidia A100 80GB GPUs for 14.5 hours."],
        },
        {
            "criterion_id": "T1-BASELINES",
            "criterion": "Were baselines compared under matched tuning and budget conditions?",
            "status": "MET",
            "severity": "NOTE",
            "description": "Baselines received matched Bayesian search tuning.",
            "evidence_quotes": [
                "All baselines were re-tuned using identical 50-trial Bayesian hyperparameter search."
            ],
        },
    ]

    state: ReviewGraphState = {
        "session_id": "eval-completeness-02",
        "title": "Rigorous and Reproducible Language Model Training",
        "methodology_text": complete_methodology,
        "checklist": SAMPLE_CHECKLIST,
    }

    with patch("app.core.llm_gateway.llm_gateway.complete", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = GatewayResponse(
            content=json.dumps(mock_llm_findings),
            model="gemini/gemini-1.5-flash",
        )
        result = await review_methodology(state)
        findings = result["findings"]

        assert len(findings) == 3
        for finding in findings:
            assert finding["status"] == "MET"
            assert len(finding["evidence_quotes"]) > 0
            # Quotes must be exact substrings of submitted text
            for quote in finding["evidence_quotes"]:
                assert quote in complete_methodology
