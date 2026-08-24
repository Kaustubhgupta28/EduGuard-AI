import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def generate_viva_questions(doc_profile: dict, raw_text: str, groq_api_key: str) -> list:
    """
    Generate 3-level viva questions based on the submission topic.
    Basic → Intermediate → Advanced
    """
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.7)

    topic        = doc_profile.get("topic", "General Topic")
    concepts     = doc_profile.get("key_concepts", [])
    has_math     = doc_profile.get("has_math", False)
    has_code     = doc_profile.get("has_code", False)
    subject_area = doc_profile.get("subject_area", "")

    system_prompt = """You are an expert academic examiner conducting a viva voce.
Generate exactly 6 viva questions for the given topic — 2 Basic, 2 Intermediate, 2 Advanced.

Return ONLY valid JSON array:
[
  {
    "level": "Basic",
    "question": "...",
    "expected_keywords": ["keyword1", "keyword2", "keyword3"],
    "marks": 2
  },
  ...
]

Guidelines:
- Basic: definitions, recall, simple explanations
- Intermediate: application, reasoning, comparisons
- Advanced: mathematical depth, edge cases, critical analysis
- Questions must directly relate to the submission content
Return ONLY the JSON array. No markdown. No explanation."""

    user_prompt = f"""Topic: {topic}
Subject Area: {subject_area}
Key Concepts: {', '.join(concepts)}
Has Math: {has_math}
Has Code: {has_code}

Submission excerpt (first 1500 chars):
{raw_text[:1500]}

Generate 6 viva questions."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    try:
        questions = json.loads(response.content.strip())
        return questions
    except Exception:
        # Fallback questions
        return [
            {"level": "Basic",        "question": f"What is {topic}? Explain in your own words.", "expected_keywords": concepts[:2], "marks": 2},
            {"level": "Basic",        "question": f"What are the main components of {topic}?",     "expected_keywords": concepts[1:3], "marks": 2},
            {"level": "Intermediate", "question": f"How does {topic} solve real-world problems? Give an example.", "expected_keywords": concepts, "marks": 3},
            {"level": "Intermediate", "question": f"What are the limitations of {topic}?",         "expected_keywords": [], "marks": 3},
            {"level": "Advanced",     "question": f"Critically analyze the architecture/design decisions in {topic}.", "expected_keywords": [], "marks": 5},
            {"level": "Advanced",     "question": f"How would you extend or improve {topic}?",     "expected_keywords": [], "marks": 5},
        ]


def evaluate_answer(question: str, student_answer: str, expected_keywords: list,
                    marks: int, groq_api_key: str) -> dict:
    """
    Evaluate a single student answer using LLM.
    Returns score, feedback, and missing concepts.
    """
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.2)

    system_prompt = """You are a strict but fair academic evaluator.
Evaluate the student's answer and return ONLY valid JSON:
{
  "score": <integer between 0 and max_marks>,
  "max_marks": <max_marks>,
  "understanding_level": "Poor / Basic / Moderate / Good / Excellent",
  "feedback": "1-2 sentence constructive feedback",
  "missing_concepts": ["concept1", "concept2"],
  "correct_concepts": ["concept1"]
}
Return ONLY JSON. No markdown."""

    user_prompt = f"""Question: {question}
Max Marks: {marks}
Expected Keywords: {', '.join(expected_keywords) if expected_keywords else 'Not specified'}

Student's Answer: {student_answer}

Evaluate the answer."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    try:
        return json.loads(response.content.strip())
    except Exception:
        return {
            "score": 0,
            "max_marks": marks,
            "understanding_level": "Unknown",
            "feedback": "Could not evaluate answer.",
            "missing_concepts": [],
            "correct_concepts": []
        }


def run_verification_agent(state: dict) -> dict:
    """
    Knowledge Verification Agent:
    - Generates viva questions (Basic / Intermediate / Advanced)
    - Collects student answers interactively via CLI
    - Evaluates each answer
    - Computes overall understanding score
    """
    doc_profile  = state.get("doc_profile", {})
    raw_text     = state.get("raw_text", "")
    groq_api_key = state.get("groq_api_key")

    print("[Knowledge Verification Agent] Generating viva questions...\n")

    questions = generate_viva_questions(doc_profile, raw_text, groq_api_key)

    topic = doc_profile.get("topic", "your submission")
    print("=" * 60)
    print(f"  VIVA SESSION — Topic: {topic}")
    print("=" * 60)
    print("  Answer each question honestly. This evaluates your understanding.\n")

    results       = []
    total_score   = 0
    total_marks   = 0
    weak_concepts = []

    for i, q in enumerate(questions, 1):
        level    = q.get("level", "")
        question = q.get("question", "")
        keywords = q.get("expected_keywords", [])
        marks    = q.get("marks", 2)

        print(f"\n  Q{i} [{level}] ({marks} marks)")
        print(f"  {question}")
        print()

        student_answer = input("  Your Answer: ").strip()

        if not student_answer:
            student_answer = "(No answer provided)"

        print("  Evaluating...", end="\r")

        evaluation = evaluate_answer(question, student_answer, keywords, marks, groq_api_key)

        score     = evaluation.get("score", 0)
        max_marks = evaluation.get("max_marks", marks)
        level_tag = evaluation.get("understanding_level", "Unknown")

        total_score += score
        total_marks += max_marks

        print(f"  Score     : {score}/{max_marks}  |  Understanding: {level_tag}")
        print(f"  Feedback  : {evaluation.get('feedback', '')}")

        if evaluation.get("missing_concepts"):
            weak_concepts.extend(evaluation["missing_concepts"])
            print(f"  Missing   : {', '.join(evaluation['missing_concepts'])}")

        results.append({
            "question_no": i,
            "level": level,
            "question": question,
            "student_answer": student_answer,
            "evaluation": evaluation,
        })

    # ── Overall Score ──
    percentage = round((total_score / total_marks) * 100, 1) if total_marks > 0 else 0

    if percentage >= 80:
        understanding = "Excellent"
    elif percentage >= 60:
        understanding = "Good"
    elif percentage >= 40:
        understanding = "Moderate"
    else:
        understanding = "Poor"

    print("\n" + "=" * 60)
    print(f"  VIVA COMPLETE")
    print(f"  Score          : {total_score}/{total_marks} ({percentage}%)")
    print(f"  Understanding  : {understanding}")
    print("=" * 60)
    print("[Knowledge Verification Agent] Done.\n")

    return {
        **state,
        "viva_results": {
            "questions_and_answers": results,
            "total_score": total_score,
            "total_marks": total_marks,
            "percentage": percentage,
            "understanding_level": understanding,
            "weak_concepts": list(set(weak_concepts)),
        }
    }
