"""Prompts for qualitative overall methodology assessment synthesis."""

ASSESSMENT_SYSTEM_PROMPT = """You are an expert computer science research methodology evaluator.
Your task is to synthesize the review findings and cross-section consistency results into a balanced qualitative overall assessment.

Strict Product Constraints:
1. You MUST assign one of the following exact qualitative labels:
   - "Well documented" — The methodology is thoroughly detailed; almost all criteria are met with clear empirical specifications.
   - "Partially documented" — The core approach is described, but notable parameters, compute details, or evaluation baselines are incomplete or missing.
   - "Insufficiently documented" — Major methodological components are missing or vague; reproducing or verifying the work would be substantially impaired.
2. NO NUMERICAL SCORES: Do not output percentages, points, or numeric grades anywhere in your response.
3. NO CLAIMS OF SCIENTIFIC VALIDITY: The assessment evaluates reporting completeness, not whether the theoretical claims of the paper are correct or valid.

You MUST respond ONLY with valid JSON in this exact structure:
{
  "label": "Well documented" | "Partially documented" | "Insufficiently documented",
  "summary": "string explaining the assessment based strictly on the findings",
  "strengths": ["string"],
  "critical_gaps": ["string"]
}
"""

def build_assessment_prompt(
    findings: list[dict],
    inconsistencies: list[dict],
    primary_paradigm: str | None,
) -> str:
    """Build user prompt for qualitative overall assessment synthesis."""
    met_count = sum(1 for f in findings if f.get("status") == "MET")
    incomplete_count = sum(1 for f in findings if f.get("status") == "INCOMPLETE")
    missing_count = sum(1 for f in findings if f.get("status") == "MISSING")
    critical_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")

    summary_stats = (
        f"Research Paradigm: {primary_paradigm or 'General AI'}\n"
        f"Findings Summary: {met_count} MET, {incomplete_count} INCOMPLETE, {missing_count} MISSING "
        f"({critical_count} CRITICAL severity issues).\n"
        f"Inconsistencies Identified: {len(inconsistencies)}"
    )

    findings_detail = "\n".join(
        f"- [{f.get('status')}] {f.get('criterion')}: {f.get('description')} (Severity: {f.get('severity')})"
        for f in findings
    )

    inconsistencies_detail = "\n".join(
        f"- Discrepancy between {', '.join(inc.get('sections_involved', []))}: {inc.get('description')}"
        for inc in inconsistencies
    ) if inconsistencies else "None identified."

    return (
        f"{summary_stats}\n\n"
        f"=== Detailed Findings ===\n{findings_detail}\n\n"
        f"=== Inconsistencies ===\n{inconsistencies_detail}"
    )
