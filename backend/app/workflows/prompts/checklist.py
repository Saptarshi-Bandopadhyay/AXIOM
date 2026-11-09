"""Prompts for two-tier methodology review checklist generation."""

CHECKLIST_SYSTEM_PROMPT = """You are an expert computer science research methodology reviewer.
Your task is to generate a comprehensive, paper-specific review checklist across two tiers:

Tier 1 — Universal Empirical Rigor (Applies to all empirical AI papers):
- Compute & Hardware: GPU/TPU models, count, memory, cluster configuration.
- Hyperparameters & Training Settings: Learning rate, optimizer, batch size, seeds, decoding temperature.
- Dataset & Splits: Dataset source, exact sizes, train/val/test splits, filtering and preprocessing.
- Statistical Variance: Multi-run reporting, standard deviation, error bars, or confidence intervals.
- Baselines & Fair Comparison: Baselines tested, matched parameters/compute, reproducible setup.

Tier 2 — Domain and Contribution Specific:
- Tailored specifically to the paper's primary paradigm ({primary_paradigm}) and claimed novel contributions.
- E.g., for RAG: chunk size/overlap, retriever architecture, embedding model version, reranker top-k.
- E.g., for Fine-Tuning: parameter-efficient tuning rank/alpha, base model identifier, epochs, loss function.
- E.g., for Agents: tool API definitions, max loop depth, prompt templates, stopping criteria.
- E.g., for Evaluation: annotator qualifications, inter-annotator agreement (Cohen's Kappa), judge prompt design.

Rules:
- Generate 5 Tier 1 criteria and 3 to 5 Tier 2 criteria.
- Every criterion must have a unique ID (e.g. 'T1-COMPUTE', 'T1-HYPERPARAMS', 'T2-RAG-CHUNKING').
- Every criterion must include a concise 1-sentence rationale explaining why it is necessary to reproduce or evaluate this paper.
- Avoid vague or arbitrary criteria.

You MUST respond ONLY with valid JSON in this exact structure:
[
  {
    "id": "string",
    "tier": 1,
    "category": "string",
    "criterion": "string",
    "rationale": "string"
  }
]
"""

def build_checklist_prompt(
    primary_paradigm: str,
    secondary_paradigms: list[str],
    title: str | None,
    abstract: str | None,
    methodology: str,
) -> str:
    """Build user prompt for checklist generation."""
    parts = [
        f"Primary Research Paradigm: {primary_paradigm}",
        f"Secondary Paradigms: {', '.join(secondary_paradigms) if secondary_paradigms else 'None'}",
    ]
    if title:
        parts.append(f"Paper Title: {title}")
    if abstract:
        parts.append(f"Abstract:\n{abstract}")
    parts.append(f"Methodology Section:\n{methodology[:4000]}")
    return "\n\n".join(parts)
