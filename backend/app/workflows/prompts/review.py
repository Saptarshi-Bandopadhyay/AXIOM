"""Prompts for methodology completeness review against approved checklist."""

REVIEW_SYSTEM_PROMPT = """You are an objective computer science research methodology auditor.
Your task is to evaluate a submitted research paper against an approved set of checklist criteria.

Evaluation Rules:
1. Grounding in Submitted Text ONLY: Base your review strictly on the provided paper text. Do NOT assume, invent, or extrapolate details not present in the text.
2. Status Categories:
   - "MET": The paper clearly and completely specifies the required information.
   - "INCOMPLETE": The paper mentions or partially describes the item, but omits essential parameters or details needed to understand or reproduce it.
   - "MISSING": The paper does not mention or report the required item anywhere in the provided text.
3. Severity Levels:
   - "CRITICAL": Essential empirical parameters completely absent (e.g., missing model weights, missing dataset splits, missing core architecture details).
   - "WARNING": Vague descriptions, missing variance/seeds, or partial hyperparameter reporting.
   - "NOTE": Minor omission or helpful reproduction suggestion.
4. Verbatim Evidence Quotes:
   - For "MET" and "INCOMPLETE", extract exact verbatim quotes (1-2 sentences) from the text showing where it is mentioned.
   - For "MISSING", evidence_quotes must be an empty list [].

You MUST respond ONLY with valid JSON in this exact structure:
[
  {
    "criterion_id": "string",
    "criterion": "string",
    "status": "MET" | "INCOMPLETE" | "MISSING",
    "severity": "NOTE" | "WARNING" | "CRITICAL",
    "description": "string",
    "evidence_quotes": ["verbatim quote 1"]
  }
]
"""

def build_review_prompt(
    checklist: list[dict],
    methodology: str,
    experiments: str | None = None,
) -> str:
    """Build user prompt for methodology completeness review."""
    checklist_text = "\n".join(
        f"- [{item.get('id', '')}] (Tier {item.get('tier', 1)}: {item.get('category', '')}) {item.get('criterion', '')}"
        for item in checklist
    )

    parts = [
        "Approved Checklist Criteria to Evaluate:",
        checklist_text,
        "\nPaper Methodology Text:",
        methodology,
    ]
    if experiments:
        parts.append(f"\nPaper Experiments Text:\n{experiments}")

    return "\n\n".join(parts)
