from typing import TypedDict, Any
from langgraph.graph import StateGraph, END

from agents.submission_agent import run_submission_agent
from agents.ai_detection_agent import run_ai_detection_agent
from agents.verification_agent import run_verification_agent
from agents.feedback_agent import run_feedback_agent
from agents.coach_agent import run_coach_agent


# ─────────────────────────────────────────────
#  State Schema
# ─────────────────────────────────────────────

class EduGuardState(TypedDict, total=False):
    # Input
    file_path:     str
    groq_api_key:  str

    # Submission Agent output
    file_data:     dict
    raw_text:      str
    doc_profile:   dict

    # AI Detection Agent output
    ai_detection:  dict

    # Verification Agent output
    viva_results:  dict

    # Feedback Agent output
    feedback:      dict

    # Coach Agent output
    study_roadmap: dict

    # Error handling
    error:         str


# ─────────────────────────────────────────────
#  Routing Logic
# ─────────────────────────────────────────────

def route_after_submission(state: EduGuardState) -> str:
    """If submission failed, go to END. Else proceed to AI Detection."""
    if state.get("error"):
        return END
    return "ai_detection"


# ─────────────────────────────────────────────
#  Build the Graph
# ─────────────────────────────────────────────

def build_eduguard_graph() -> StateGraph:
    graph = StateGraph(EduGuardState)

    # ── Add all agent nodes ──
    graph.add_node("submission",    run_submission_agent)
    graph.add_node("ai_detection",  run_ai_detection_agent)
    graph.add_node("verification",  run_verification_agent)
    graph.add_node("feedback",      run_feedback_agent)
    graph.add_node("coach",         run_coach_agent)

    # ── Entry point ──
    graph.set_entry_point("submission")

    # ── Conditional edge after submission ──
    graph.add_conditional_edges(
        "submission",
        route_after_submission,
        {
            "ai_detection": "ai_detection",
            END: END,
        }
    )

    # ── Linear pipeline after AI detection ──
    graph.add_edge("ai_detection", "verification")
    graph.add_edge("verification", "feedback")
    graph.add_edge("feedback",     "coach")
    graph.add_edge("coach",        END)

    return graph.compile()


# ─────────────────────────────────────────────
#  Run the pipeline
# ─────────────────────────────────────────────

def run_eduguard_pipeline(file_path: str, groq_api_key: str) -> dict:
    """
    Entry point for the full EduGuard AI pipeline.
    Returns the final state with all agent outputs.
    """
    app = build_eduguard_graph()

    initial_state = {
        "file_path":    file_path,
        "groq_api_key": groq_api_key,
    }

    final_state = app.invoke(initial_state)
    return final_state
