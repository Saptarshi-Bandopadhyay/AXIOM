"""Prompts for cross-section inconsistency detection."""

CONSISTENCY_SYSTEM_PROMPT = """You are an expert scientific auditor detecting factual discrepancies across paper sections.
Your task is to compare the paper's Methodology, Experiments, and Results sections to identify any internal contradictions.

Examples of inconsistencies:
- Methodology describes chunk size as 512 tokens, but experiments state chunk size was set to 1024 tokens.
- Methodology claims 5-fold cross validation on dataset X, but results only report numbers for dataset Y.
- Methodology introduces a loss function with hyperparameter alpha=0.5, but experiments tabulate alpha=0.1.

Strict Rules:
1. Grounding: Only report an inconsistency when there is explicit conflicting evidence in the text. Do NOT speculate or flag differences that are clearly intentional ablations.
2. If no inconsistencies are found, return an empty list [].
3. For each inconsistency, provide exact verbatim quotes from the conflicting sections demonstrating the discrepancy.

You MUST respond ONLY with valid JSON in this exact structure:
[
  {
    "sections_involved": ["methodology", "experiments"],
    "description": "string explaining the discrepancy",
    "evidence_quotes": ["verbatim quote from section A", "verbatim quote from section B"]
  }
]
"""

def build_consistency_prompt(
    methodology: str,
    experiments: str | None,
    results: str | None,
) -> str:
    """Build user prompt for cross-section consistency check."""
    parts = [f"=== Methodology Section ===\n{methodology}"]
    if experiments:
        parts.append(f"=== Experiments Section ===\n{experiments}")
    if results:
        parts.append(f"=== Results Section ===\n{results}")

    return "\n\n".join(parts)
