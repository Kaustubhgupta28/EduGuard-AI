import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def run_coach_agent(state: dict) -> dict:
    """
    Learning Coach Agent:
    - Reads weak concepts from viva + feedback
    - Generates a day-by-day personalized study roadmap
    - Recommends specific resources per topic
    """
    doc_profile  = state.get("doc_profile", {})
    viva_results = state.get("viva_results", {})
    feedback     = state.get("feedback", {})
    groq_api_key = state.get("groq_api_key")

    print("[Learning Coach Agent] Building personalized study roadmap...\n")

    topic           = doc_profile.get("topic", "your subject")
    subject_area    = doc_profile.get("subject_area", "")
    key_concepts    = doc_profile.get("key_concepts", [])
    weak_concepts   = viva_results.get("weak_concepts", [])
    understanding   = viva_results.get("understanding_level", "Moderate")
    areas_to_improve = feedback.get("student_feedback", {}).get("areas_to_improve", [])

    # Combine all weak areas
    all_weak = list(set(weak_concepts + areas_to_improve))
    if not all_weak:
        all_weak = key_concepts[:3]

    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.6)

    system_prompt = """You are an expert academic learning coach.
Create a personalized 7-day study roadmap for a student.
Return ONLY valid JSON:
{
  "roadmap_title": "Title for the study plan",
  "total_days": 7,
  "daily_plan": [
    {
      "day": 1,
      "focus_topic": "Topic name",
      "goal": "What student should achieve today",
      "tasks": ["task1", "task2", "task3"],
      "resources": [
        {"type": "Video", "title": "Resource name", "platform": "YouTube/Coursera/etc"},
        {"type": "Article", "title": "Resource name", "platform": "Platform name"}
      ],
      "practice": "1 specific practice exercise"
    }
  ],
  "final_milestone": "What the student should be able to do after 7 days",
  "motivational_note": "Short encouraging message"
}
Return ONLY JSON. No markdown. No explanation."""

    user_prompt = f"""Student's topic: {topic}
Subject area: {subject_area}
Current understanding level: {understanding}
Weak concepts identified: {', '.join(all_weak)}
Key concepts in submission: {', '.join(key_concepts)}

Create a 7-day personalized study roadmap targeting the weak areas."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    try:
        roadmap = json.loads(response.content.strip())
    except Exception:
        roadmap = {
            "roadmap_title": f"7-Day Recovery Plan: {topic}",
            "total_days": 7,
            "daily_plan": [
                {
                    "day": i + 1,
                    "focus_topic": all_weak[i % len(all_weak)] if all_weak else f"Topic {i+1}",
                    "goal": f"Understand {all_weak[i % len(all_weak)] if all_weak else 'core concepts'}",
                    "tasks": ["Read documentation", "Watch tutorial", "Practice problems"],
                    "resources": [
                        {"type": "Video", "title": "Search on YouTube", "platform": "YouTube"},
                        {"type": "Article", "title": "Search on Google", "platform": "Web"}
                    ],
                    "practice": "Solve 2-3 practice problems on this topic."
                }
                for i in range(7)
            ],
            "final_milestone": f"Strong conceptual understanding of {topic}",
            "motivational_note": "Every expert was once a beginner. Keep going!"
        }

    # ── Print Roadmap ──
    print(f"  📚 {roadmap.get('roadmap_title')}")
    print()

    for day_plan in roadmap.get("daily_plan", []):
        day     = day_plan.get("day")
        focus   = day_plan.get("focus_topic")
        goal    = day_plan.get("goal")
        tasks   = day_plan.get("tasks", [])
        resources = day_plan.get("resources", [])
        practice  = day_plan.get("practice")

        print(f"  Day {day} — {focus}")
        print(f"    Goal     : {goal}")
        print(f"    Tasks    : {' | '.join(tasks)}")
        print(f"    Resources: {', '.join(r['title'] + ' (' + r['platform'] + ')' for r in resources)}")
        print(f"    Practice : {practice}")
        print()

    print(f"  🎯 Final Milestone: {roadmap.get('final_milestone')}")
    print(f"  💬 {roadmap.get('motivational_note')}")
    print()
    print("[Learning Coach Agent] Done.\n")

    return {
        **state,
        "study_roadmap": roadmap,
    }
