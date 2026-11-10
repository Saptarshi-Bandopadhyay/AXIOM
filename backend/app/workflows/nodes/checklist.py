"""Checklist generation node for LangGraph workflow."""

import json
import logging
import re
from typing import Any
from app.core.llm_gateway import llm_gateway
from app.workflows.prompts.checklist import (
    CHECKLIST_SYSTEM_PROMPT,
    build_checklist_prompt,
)
from app.workflows.state import ChecklistItem, ReviewGraphState

logger = logging.getLogger(__name__)

# Default fallback Tier 1 checklist if generation encounters an error
FALLBACK_TIER1_CHECKLIST: list[dict[str, Any]] = [
    {
        "id": "T1-COMPUTE-1",
        "tier": 1,
        "category": "Compute & Hardware",
        "criterion": "Does the paper report the specific hardware specifications, GPU/TPU models, count, and memory used?",
        "rationale": "Hardware specification is necessary to verify computational feasibility and resource consumption.",
        "approved": True,
    },
    {
        "id": "T1-HYPERPARAMS-1",
        "tier": 1,
        "category": "Hyperparameters",
        "criterion": "Are training hyperparameters (learning rates, batch sizes, optimizers, and random seeds) clearly documented?",
        "rationale": "Hyperparameter reporting ensures researchers can reproduce identical optimization dynamics.",
        "approved": True,
    },
    {
        "id": "T1-DATASET-1",
        "tier": 1,
        "category": "Dataset Details",
        "criterion": "Does the paper state dataset sources, exact training/validation/test sample counts, and preprocessing steps?",
        "rationale": "Dataset details ensure data splits and filtering methods can be matched identically.",
        "approved": True,
    },
    {
        "id": "T1-VARIANCE-1",
        "tier": 1,
        "category": "Statistical Variance",
        "criterion": "Does the paper report results across multiple runs with standard deviations, variance, or confidence intervals?",
        "rationale": "Multi-run variance confirms whether measured performance gains are statistically meaningful.",
        "approved": True,
    },
    {
        "id": "T1-BASELINES-1",
        "tier": 1,
        "category": "Baselines & Fairness",
        "criterion": "Are baseline comparisons evaluated under matched parameters, identical test splits, and fair compute conditions?",
        "rationale": "Fair baseline calibration prevents misleading superiority claims.",
        "approved": True,
    },
]


def _extract_json_list(text: str) -> list[dict[str, Any]]:
    """Parse JSON list of items from LLM response text."""
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", cleaned)
        if match:
            cleaned = match.group(1)
    return json.loads(cleaned)


async def generate_checklist(state: ReviewGraphState) -> dict[str, Any]:
    """Generate Tier 1 and Tier 2 criteria tailored to the paper's research paradigm."""
    primary_paradigm = state.get("primary_research_type") or "General / Novel AI Research"
    secondary_paradigms = state.get("secondary_research_types") or []

    system_prompt = CHECKLIST_SYSTEM_PROMPT.replace("{primary_paradigm}", primary_paradigm)
    prompt = build_checklist_prompt(
        primary_paradigm=primary_paradigm,
        secondary_paradigms=secondary_paradigms,
        title=state.get("title"),
        abstract=state.get("abstract_text"),
        methodology=state.get("methodology_text", ""),
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    try:
        response = await llm_gateway.complete(
            messages=messages,
            span_name="workflow_generate_checklist",
            temperature=0.0,
        )
        raw_items = _extract_json_list(response.content)

        # Validate with Pydantic ChecklistItem schema
        validated_items: list[dict[str, Any]] = []
        for idx, item in enumerate(raw_items):
            if isinstance(item, str):
                item = {"criterion": item, "category": "Methodology", "rationale": "Empirical check."}
            item_id = item.get("id") or f"CRIT-{idx + 1}"
            validated = ChecklistItem(
                id=item_id,
                tier=item.get("tier", 1 if idx < 5 else 2),
                category=item.get("category", "Methodology"),
                criterion=item.get("criterion", ""),
                rationale=item.get("rationale", ""),
                approved=True,
            )
            validated_items.append(validated.model_dump())

        return {"checklist": validated_items}
    except Exception as exc:
        logger.error("Checklist generation failed: %s. Using default Tier 1 checklist.", exc)
        return {"checklist": FALLBACK_TIER1_CHECKLIST}
