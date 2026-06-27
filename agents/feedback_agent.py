import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def run_feedback_agent(state: dict) -> dict:
    """
    Feedback Agent:
    - Reads viva results + AI detection scores
    - Generates personalized student feedback (mentor tone)
    - Generates professor evaluation report
    """
    doc_profile  = state.get("doc_profile", {})
    viva_results = state.get("viva_results", {})
    ai_detection = state.get("ai_detection", {})
    groq_api_key = state.get("groq_api_key")

    print("[Feedback Agent] Generating feedback...\n")

    topic          = doc_profile.get("topic", "submission")
    understanding  = viva_results.get("understanding_level", "Unknown")
    viva_score_pct = viva_results.get("percentage", 0)
    weak_concepts  = viva_results.get("weak_concepts", [])
    ai_score       = ai_detection.get("ai_involvement_score", 0)
    risk_level     = ai_detection.get("risk_level", "Unknown")
    semantic       = ai_detection.get("semantic_analysis", {})

    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.5)

    # ── Student Feedback ──
    student_system = """You are a supportive academic mentor.
Generate honest, constructive, encouraging feedback for a student.
Return ONLY valid JSON:
{
  "overall_message": "2-3 sentences summarizing performance",
  "strengths": ["strength1", "strength2"],
  "areas_to_improve": ["area1", "area2", "area3"],
  "immediate_action": "1 specific thing to do right now",
  "encouragement": "1 motivational closing sentence"
}
Return ONLY JSON. No markdown."""

    student_user = f"""Student submitted: {topic}
Viva Score: {viva_score_pct}% ({understanding} understanding)
AI Involvement: {ai_score}% ({risk_level} risk)
Weak Concepts: {', '.join(weak_concepts) if weak_concepts else 'None identified'}
Writing Style: {semantic.get('writing_style', 'Unknown')}
Red Flags: {', '.join(semantic.get('red_flags', [])) if semantic.get('red_flags') else 'None'}

Generate student feedback."""

    s_response = llm.invoke([
        SystemMessage(content=student_system),
        HumanMessage(content=student_user)
    ])

    try:
        student_feedback = json.loads(s_response.content.strip())
    except Exception:
        student_feedback = {
            "overall_message": f"Your viva performance shows {understanding} understanding of {topic}.",
            "strengths": ["Attempted all questions"],
            "areas_to_improve": weak_concepts[:3] if weak_concepts else ["Review core concepts"],
            "immediate_action": "Review the weak topics identified above.",
            "encouragement": "Keep learning — improvement comes with consistent effort!"
        }

    # ── Professor Report ──
    prof_system = """You are an academic integrity evaluation system.
Generate a concise professor evaluation report.
Return ONLY valid JSON:
{
  "summary": "2-3 sentence overall assessment",
  "ai_usage_assessment": "Clear statement about AI involvement",
  "understanding_assessment": "Statement about conceptual depth",
  "integrity_concern_level": "None / Low / Moderate / High",
  "recommended_action": "Pass / Additional Viva / Detailed Review / Flag for Review",
  "notes_for_professor": "1-2 specific observations"
}
Return ONLY JSON. No markdown."""

    prof_user = f"""Student Submission: {topic}
AI Involvement Score: {ai_score}% — {ai_detection.get('label', '')}
Risk Level: {risk_level}
Viva Score: {viva_score_pct}% — {understanding} understanding
Weak Concepts: {', '.join(weak_concepts) if weak_concepts else 'None'}
Writing Style Issues: {', '.join(semantic.get('red_flags', [])) if semantic.get('red_flags') else 'None'}
Citation Status: {semantic.get('citation_authenticity', 'Unknown')}

Generate professor evaluation report."""

    p_response = llm.invoke([
        SystemMessage(content=prof_system),
        HumanMessage(content=prof_user)
    ])

    try:
        professor_report = json.loads(p_response.content.strip())
    except Exception:
        professor_report = {
            "summary": f"Student shows {understanding} understanding with {ai_score}% AI involvement.",
            "ai_usage_assessment": f"AI involvement estimated at {ai_score}% ({risk_level} risk).",
            "understanding_assessment": f"Viva score: {viva_score_pct}%.",
            "integrity_concern_level": risk_level,
            "recommended_action": "Additional Viva" if ai_score > 60 else "Pass",
            "notes_for_professor": "Review weak concepts identified during viva."
        }

    # ── Print Summary ──
    print("  ── STUDENT FEEDBACK ──")
    print(f"  {student_feedback.get('overall_message')}")
    print(f"  Strengths         : {', '.join(student_feedback.get('strengths', []))}")
    print(f"  Improve           : {', '.join(student_feedback.get('areas_to_improve', []))}")
    print(f"  Action            : {student_feedback.get('immediate_action')}")
    print()
    print("  ── PROFESSOR REPORT ──")
    print(f"  {professor_report.get('summary')}")
    print(f"  Integrity Concern : {professor_report.get('integrity_concern_level')}")
    print(f"  Recommendation    : {professor_report.get('recommended_action')}")
    print()
    print("[Feedback Agent] Done.\n")

    return {
        **state,
        "feedback": {
            "student_feedback": student_feedback,
            "professor_report": professor_report,
        }
    }
