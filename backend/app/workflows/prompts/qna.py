"""Prompts for grounded question answering on submitted papers and review findings."""

QNA_SYSTEM_PROMPT = """You are ReproCheck Grounded Q&A assistant.
Your task is to answer user questions strictly based on the submitted research paper and its methodology review findings.

Strict Scope Constraints:
1. Strict Grounding: Use ONLY the provided paper text, review findings, checklist, inconsistencies, and overall assessment.
2. Citation of Evidence: Always cite verbatim evidence quotes or specific section references when making claims.
3. Out-of-Scope Refusal: If the user asks a question unrelated to this paper or review (e.g. general knowledge, trivia, coding exercises, or general opinion), politely decline:
   "I can only answer questions directly related to the submitted paper and its methodology review findings."
4. No Hallucinations: If the paper does not mention an answer, explicitly state:
   "The submitted paper does not provide information regarding this topic."
"""

def build_qna_prompt(
    question: str,
    methodology: str,
    experiments: str | None,
    results: str | None,
    findings: list[dict],
    assessment: dict | None,
) -> str:
    """Build user prompt for grounded Q&A."""
    parts = [
        f"=== User Question ===\n{question}\n",
        f"=== Submitted Paper Methodology ===\n{methodology[:3000]}",
    ]
    if experiments:
        parts.append(f"=== Submitted Paper Experiments ===\n{experiments[:2000]}")
    if results:
        parts.append(f"=== Submitted Paper Results ===\n{results[:1500]}")

    if assessment:
        parts.append(f"=== Overall Assessment ===\nLabel: {assessment.get('label')}\nSummary: {assessment.get('summary')}")

    if findings:
        findings_summary = "\n".join(
            f"- [{f.get('status')}] {f.get('criterion')}: {f.get('description')}"
            for f in findings[:10]
        )
        parts.append(f"=== Key Review Findings ===\n{findings_summary}")

    return "\n\n".join(parts)
