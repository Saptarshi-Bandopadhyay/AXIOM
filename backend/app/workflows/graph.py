"""LangGraph review workflow engine for ReproCheck.

Constructs and compiles the StateGraph connecting classification, checklist generation,
human-in-the-loop pause (interrupt), methodology review, consistency checking,
and qualitative overall assessment.
"""

from typing import Any
from langgraph.graph import END, START, StateGraph
from app.workflows.nodes.approval import human_approval
from app.workflows.nodes.assessment import synthesize_overall_assessment
from app.workflows.nodes.checklist import generate_checklist
from app.workflows.nodes.classify import classify_research_paradigm
from app.workflows.nodes.consistency import check_cross_section_consistency
from app.workflows.nodes.review import review_methodology
from app.workflows.state import ReviewGraphState


def create_review_workflow(checkpointer: Any | None = None) -> Any:
    """Construct and compile the LangGraph review state machine.

    Args:
        checkpointer: State checkpointer (e.g. MemorySaver or PostgresSaver).

    Returns:
        CompiledStateGraph: Executable workflow graph.
    """
    builder = StateGraph(ReviewGraphState)

    # Register workflow nodes
    builder.add_node("classify", classify_research_paradigm)
    builder.add_node("generate_checklist", generate_checklist)
    builder.add_node("human_approval", human_approval)
    builder.add_node("review_methodology", review_methodology)
    builder.add_node("check_consistency", check_cross_section_consistency)
    builder.add_node("synthesize_assessment", synthesize_overall_assessment)

    # Sequence edges
    builder.add_edge(START, "classify")
    builder.add_edge("classify", "generate_checklist")
    builder.add_edge("generate_checklist", "human_approval")
    builder.add_edge("human_approval", "review_methodology")
    builder.add_edge("review_methodology", "check_consistency")
    builder.add_edge("check_consistency", "synthesize_assessment")
    builder.add_edge("synthesize_assessment", END)

    return builder.compile(checkpointer=checkpointer)
