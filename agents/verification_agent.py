import json
import random
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def generate_viva_questions(doc_profile: dict, raw_text: str, groq_api_key: str) -> list:
    """
    Generate 9 MCQ + 1 Short Answer question.
    High temperature = different questions every run.
    """
    # Random seed in prompt = different questions every time
    rand_seed = random.randint(1000, 9999)

    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.95)

    topic        = doc_profile.get("topic", "General Topic")
    concepts     = doc_profile.get("key_concepts", [])
    subject_area = doc_profile.get("subject_area", "")
    has_math     = doc_profile.get("has_math", False)
    has_code     = doc_profile.get("has_code", False)

    system_prompt = """You are an expert academic examiner.
Generate exactly 10 questions based on the given topic and submission content.

RULES:
- Questions 1-9: MCQ type (4 options each, exactly 1 correct)
- Question 10: Short answer type (answer in 1-2 sentences)
- Every run must generate DIFFERENT questions (use the random seed for variation)
- MCQs must cover different concepts — no repetition
- Options must be plausible but clearly have one best answer
- Difficulty: mix of Basic (Q1-Q3), Intermediate (Q4-Q6), Advanced (Q7-Q9)

Return ONLY valid JSON array, exactly like this:
[
  {
    "type": "mcq",
    "level": "Basic",
    "question": "Question text here?",
    "options": {
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    },
    "correct_option": "A",
    "correct_answer": "Full correct answer text",
    "marks": 1
  },
  {
    "type": "short",
    "level": "Advanced",
    "question": "Short answer question here?",
    "expected_keywords": ["keyword1", "keyword2"],
    "marks": 3
  }
]

Return ONLY the JSON array. No markdown. No explanation. No backticks."""

    user_prompt = f"""Topic: {topic}
Subject Area: {subject_area}
Key Concepts: {', '.join(concepts)}
Has Math: {has_math}
Has Code: {has_code}
Random Seed (for variation): {rand_seed}

Submission content (first 2000 chars):
{raw_text[:2000]}

Generate 9 MCQs + 1 Short Answer question. Make them UNIQUE every time."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    try:
        # Clean response
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        questions = json.loads(content.strip())
        return questions
    except Exception:
        # Fallback MCQs
        return [
            {
                "type": "mcq", "level": "Basic",
                "question": f"What is the primary purpose of {topic}?",
                "options": {"A": "Data storage", "B": f"Core function of {topic}", "C": "Network routing", "D": "UI rendering"},
                "correct_option": "B", "correct_answer": f"Core function of {topic}", "marks": 1
            },
            {
                "type": "mcq", "level": "Basic",
                "question": f"Which of the following is a key concept in {topic}?",
                "options": {"A": concepts[0] if concepts else "Abstraction", "B": "SQL queries", "C": "CSS styling", "D": "DNS resolution"},
                "correct_option": "A", "correct_answer": concepts[0] if concepts else "Abstraction", "marks": 1
            },
            {
                "type": "mcq", "level": "Intermediate",
                "question": f"What problem does {topic} primarily solve?",
                "options": {"A": "Memory allocation", "B": "UI rendering", "C": f"Core challenge addressed by {topic}", "D": "File compression"},
                "correct_option": "C", "correct_answer": f"Core challenge addressed by {topic}", "marks": 1
            },
            {
                "type": "short", "level": "Advanced",
                "question": f"Explain the most important aspect of {topic} in 1-2 sentences.",
                "expected_keywords": concepts[:3], "marks": 3
            }
        ]


def evaluate_mcq(question: dict, student_option: str) -> dict:
    """Evaluate MCQ answer — instant, no LLM needed."""
    correct = question.get("correct_option", "")
    is_correct = student_option.strip().upper() == correct.strip().upper()
    marks = question.get("marks", 1)
    return {
        "score": marks if is_correct else 0,
        "max_marks": marks,
        "is_correct": is_correct,
        "selected_option": student_option,
        "correct_option": correct,
        "correct_answer": question.get("correct_answer", ""),
        "understanding_level": "Good" if is_correct else "Poor",
        "feedback": "Correct!" if is_correct else f"Incorrect. Correct answer: ({correct}) {question.get('correct_answer','')}",
        "missing_concepts": [] if is_correct else [question.get("question", "")[:50]],
        "correct_concepts": [question.get("question", "")[:50]] if is_correct else [],
    }


def evaluate_short_answer(question: str, student_answer: str, expected_keywords: list,
                           marks: int, groq_api_key: str) -> dict:
    """Evaluate short answer using LLM."""
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.2)

    system_prompt = """You are a strict but fair academic evaluator.
Evaluate the student's short answer and return ONLY valid JSON:
{
  "score": <integer between 0 and max_marks>,
  "max_marks": <max_marks>,
  "understanding_level": "Poor / Basic / Moderate / Good / Excellent",
  "feedback": "1-2 sentence constructive feedback",
  "missing_concepts": ["concept1"],
  "correct_concepts": ["concept1"]
}
Return ONLY JSON. No markdown."""

    user_prompt = f"""Question: {question}
Max Marks: {marks}
Expected Keywords: {', '.join(expected_keywords) if expected_keywords else 'Not specified'}
Student Answer: {student_answer}
Evaluate."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    try:
        return json.loads(response.content.strip())
    except Exception:
        return {
            "score": 0, "max_marks": marks,
            "understanding_level": "Unknown",
            "feedback": "Could not evaluate.",
            "missing_concepts": [], "correct_concepts": []
        }


def run_verification_agent(state: dict) -> dict:
    """CLI version — runs viva in terminal."""
    doc_profile  = state.get("doc_profile", {})
    raw_text     = state.get("raw_text", "")
    groq_api_key = state.get("groq_api_key")

    print("[Knowledge Verification Agent] Generating viva questions...\n")
    questions = generate_viva_questions(doc_profile, raw_text, groq_api_key)

    topic = doc_profile.get("topic", "your submission")
    print("=" * 60)
    print(f"  VIVA SESSION — Topic: {topic}")
    print("=" * 60)

    results = []
    total_score = 0
    total_marks = 0
    weak_concepts = []

    for i, q in enumerate(questions, 1):
        qtype = q.get("type", "mcq")
        level = q.get("level", "")
        marks = q.get("marks", 1)

        print(f"\n  Q{i} [{level}] ({marks} mark{'s' if marks > 1 else ''})")
        print(f"  {q.get('question','')}")

        if qtype == "mcq":
            options = q.get("options", {})
            for k, v in options.items():
                print(f"    {k}) {v}")
            student_answer = input("\n  Your Answer (A/B/C/D): ").strip().upper()
            evaluation = evaluate_mcq(q, student_answer)
        else:
            student_answer = input("\n  Your Answer (1-2 sentences): ").strip()
            evaluation = evaluate_short_answer(
                q["question"], student_answer,
                q.get("expected_keywords", []), marks, groq_api_key
            )

        score = evaluation.get("score", 0)
        max_m = evaluation.get("max_marks", marks)
        total_score += score
        total_marks += max_m

        if evaluation.get("missing_concepts"):
            weak_concepts.extend(evaluation["missing_concepts"])

        print(f"  → {evaluation.get('feedback','')}")
        results.append({"question_no": i, "level": level, "type": qtype,
                        "question": q.get("question"), "student_answer": student_answer,
                        "evaluation": evaluation})

    percentage = round((total_score / total_marks) * 100, 1) if total_marks > 0 else 0
    understanding = "Excellent" if percentage >= 80 else "Good" if percentage >= 60 else "Moderate" if percentage >= 40 else "Poor"

    print(f"\n  VIVA COMPLETE — Score: {total_score}/{total_marks} ({percentage}%) — {understanding}")
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