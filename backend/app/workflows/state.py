"""State schema and data models for the LangGraph review workflow.

Defines the typed graph state shared across classification, checklist generation,
human approval, methodology review, consistency checking, and assessment nodes.
"""

from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    """A single methodological evaluation criterion in the review checklist."""

    id: str = Field(description="Unique identifier for the criterion (e.g., 'T1-COMPUTE-1').")
    tier: Literal[1, 2] = Field(description="Tier 1 = Universal Rigor, Tier 2 = Paradigm/Domain Specific.")
    category: str = Field(description="Evaluation category (e.g., 'Compute & Hardware', 'Hyperparameters').")
    criterion: str = Field(description="Clear, actionable question or requirement.")
    rationale: str = Field(description="Short reason why this criterion applies to this paper.")
    approved: bool = Field(default=True, description="Whether this criterion was approved by the reviewer.")


class ReviewFinding(BaseModel):
    """Evaluation finding for a specific checklist criterion."""

    criterion_id: str = Field(description="Referenced ChecklistItem ID.")
    criterion: str = Field(description="The evaluation criterion text.")
    status: Literal["MET", "INCOMPLETE", "MISSING"] = Field(
        description="MET = clearly reported; INCOMPLETE = mentioned but vague; MISSING = absent."
    )
    severity: Literal["NOTE", "WARNING", "CRITICAL"] = Field(
        description="Severity level: CRITICAL for missing essentials, WARNING for partial details, NOTE for minor."
    )
    description: str = Field(description="Explanation of what was found or what is missing.")
    evidence_quotes: list[str] = Field(
        default_factory=list,
        description="Verbatim excerpts from the submitted paper supporting this finding.",
    )


class InconsistencyItem(BaseModel):
    """Discrepancy identified between different sections of the submitted paper."""

    sections_involved: list[str] = Field(description="Sections with conflicting statements (e.g. ['methodology', 'experiments']).")
    description: str = Field(description="Detailed description of the inconsistency.")
    evidence_quotes: list[str] = Field(
        default_factory=list,
        description="Verbatim excerpts demonstrating the discrepancy.",
    )


class OverallAssessment(BaseModel):
    """Qualitative assessment synthesis of the research methodology."""

    label: Literal["Well documented", "Partially documented", "Insufficiently documented"] = Field(
        description="Qualitative label describing methodology completeness."
    )
    summary: str = Field(description="Summary narrative explaining the assigned label.")
    strengths: list[str] = Field(default_factory=list, description="Key methodological strengths identified.")
    critical_gaps: list[str] = Field(default_factory=list, description="Primary missing details or concerns.")


class ReviewGraphState(TypedDict, total=False):
    """Typed state dictionary passed through LangGraph workflow nodes."""

    # Session and Input Metadata
    session_id: str
    title: str | None
    abstract_text: str | None
    methodology_text: str
    experiments_text: str | None
    results_text: str | None
    full_text: str | None
    input_type: str  # "PDF_UPLOAD" or "PASTED_TEXT"

    # Paradigm Classification (Task 4.2)
    primary_research_type: str | None
    secondary_research_types: list[str]
    research_type_rationale: str | None

    # Checklist Generation & Human Approval (Tasks 4.3 & 4.4)
    checklist: list[dict[str, Any]]
    checklist_approved: bool

    # Review Findings & Consistency (Tasks 4.5 & 4.6)
    findings: list[dict[str, Any]]
    inconsistencies: list[dict[str, Any]]

    # Overall Assessment (Task 4.7)
    overall_assessment: dict[str, Any] | None

    # Error handling
    error: str | None
