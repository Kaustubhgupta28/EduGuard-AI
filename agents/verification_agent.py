import json
import re
import random
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


def _parse_json_robust(text: str):
    """Robust JSON parser - handles markdown fences, thinking tags, extra text."""
    # Remove thinking tags (Qwen models sometimes add <think>...</think>)
    text = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE).strip()
    # Remove markdown fences
    text = re.sub(r'^```(?:json)?', '', text.strip(), flags=re.MULTILINE).strip()
    text = re.sub(r'```$', '', text.strip(), flags=re.MULTILINE).strip()
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # Find JSON array in text
    match = re.search(r'\[[\s\S]*\]', text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    # Find JSON object in text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def generate_viva_questions(doc_profile: dict, raw_text: str, groq_api_key: str) -> list:
    """
    Generate 9 MCQs + 1 Short Answer question.
    High temperature + random seed = different questions every run.
    """
    rand_seed = random.randint(1000, 9999)
    llm = ChatGroq(api_key=groq_api_key, model="qwen/qwen3.6-27b", temperature=0.9)

    topic        = doc_profile.get("topic", "General Topic")
    concepts     = doc_profile.get("key_concepts", [])
    subject_area = doc_profile.get("subject_area", "")
    has_math     = doc_profile.get("has_math", False)
    has_code     = doc_profile.get("has_code", False)

    system_prompt = """You are an expert academic examiner. Generate exactly 10 questions.

STRICT RULES:
- Questions 1-9: MCQ type with exactly 4 options (A, B, C, D), exactly 1 correct answer
- Question 10: Short answer type (1-2 sentence answer expected)
- Cover different concepts — no repetition
- Difficulty: Basic (Q1-Q3), Intermediate (Q4-Q6), Advanced (Q7-Q9)
- Return ONLY a valid JSON array, nothing else

EXACT FORMAT (copy this structure):
[
  {
    "type": "mcq",
    "level": "Basic",
    "question": "Your question here?",
    "options": {
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    },
    "correct_option": "A",
    "correct_answer": "First option full text",
    "marks": 1
  },
  {
    "type": "short",
    "level": "Advanced",
    "question": "Your short answer question here?",
    "expected_keywords": ["keyword1", "keyword2"],
    "marks": 3
  }
]

Return ONLY the JSON array. No explanation. No markdown. No thinking."""

    user_prompt = f"""Topic: {topic}
Subject: {subject_area}
Concepts: {', '.join(concepts) if concepts else topic}
Has Math: {has_math} | Has Code: {has_code}
Seed: {rand_seed}

Content sample:
{raw_text[:2000]}

Generate 9 MCQs + 1 short answer question now."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    parsed = _parse_json_robust(response.content)

    if parsed and isinstance(parsed, list) and len(parsed) > 0:
        # Validate each question has required fields
        valid = []
        for q in parsed:
            if q.get("type") == "mcq":
                if q.get("question") and q.get("options") and q.get("correct_option"):
                    valid.append(q)
            elif q.get("type") == "short":
                if q.get("question"):
                    valid.append(q)
        if len(valid) >= 4:
            return valid

    # Fallback MCQ questions using topic from profile
    t = topic if topic and topic != "Unknown Topic" else "this subject"
    c = concepts[0] if concepts else t
    return [
        {
            "type": "mcq", "level": "Basic",
            "question": f"What is the primary purpose of {t}?",
            "options": {"A": f"Core function of {t}", "B": "Data storage only", "C": "Network communication", "D": "User interface design"},
            "correct_option": "A", "correct_answer": f"Core function of {t}", "marks": 1
        },
        {
            "type": "mcq", "level": "Basic",
            "question": f"Which of the following best describes {c}?",
            "options": {"A": "A database system", "B": f"A key concept in {t}", "C": "A programming language", "D": "A hardware component"},
            "correct_option": "B", "correct_answer": f"A key concept in {t}", "marks": 1
        },
        {
            "type": "mcq", "level": "Intermediate",
            "question": f"What problem does {t} primarily address?",
            "options": {"A": "Memory management", "B": "File compression", "C": f"The core challenge in {t}", "D": "Network latency"},
            "correct_option": "C", "correct_answer": f"The core challenge in {t}", "marks": 1
        },
        {
            "type": "mcq", "level": "Intermediate",
            "question": f"How does {t} improve upon traditional approaches?",
            "options": {"A": "By using less memory", "B": "By being simpler", "C": f"By addressing limitations of older methods in {subject_area}", "D": "By requiring more data"},
            "correct_option": "C", "correct_answer": f"By addressing limitations of older methods", "marks": 1
        },
        {
            "type": "mcq", "level": "Advanced",
            "question": f"What is a key limitation or challenge when implementing {t}?",
            "options": {"A": "Too much data required", "B": f"Computational complexity or resource requirements", "C": "Lack of documentation", "D": "Language barriers"},
            "correct_option": "B", "correct_answer": "Computational complexity or resource requirements", "marks": 1
        },
        {
            "type": "short", "level": "Advanced",
            "question": f"Explain the most important aspect of {t} and why it matters in {subject_area} in 1-2 sentences.",
            "expected_keywords": concepts[:3] if concepts else [t],
            "marks": 3
        }
    ]


def evaluate_mcq(question: dict, student_option: str) -> dict:
    """Evaluate MCQ answer instantly — no LLM needed."""
    correct = question.get("correct_option", "").strip().upper()
    selected = student_option.strip().upper() if student_option else ""
    is_correct = selected == correct
    marks = question.get("marks", 1)
    return {
        "score": marks if is_correct else 0,
        "max_marks": marks,
        "is_correct": is_correct,
        "selected_option": selected,
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
    llm = ChatGroq(api_key=groq_api_key, model="qwen/qwen3.6-27b", temperature=0.2)

    system_prompt = """You are a strict but fair academic evaluator.
Evaluate the student's short answer. Return ONLY valid JSON (no markdown, no thinking):
{
  "score": <integer 0 to max_marks>,
  "max_marks": <max_marks>,
  "understanding_level": "Poor / Basic / Moderate / Good / Excellent",
  "feedback": "1-2 sentence feedback",
  "missing_concepts": ["concept1"],
  "correct_concepts": ["concept1"]
}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Question: {question}\nMax Marks: {marks}\nExpected Keywords: {', '.join(expected_keywords)}\nStudent Answer: {student_answer}\nEvaluate.")
    ])

    parsed = _parse_json_robust(response.content)
    if parsed and isinstance(parsed, dict):
        return parsed

    return {
        "score": 0, "max_marks": marks,
        "understanding_level": "Unknown",
        "feedback": "Could not evaluate answer.",
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
    print(f"  VIVA SESSION — Topic: {topic}\n")

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
            for k, v in q.get("options", {}).items():
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

    print(f"\n  VIVA COMPLETE — {total_score}/{total_marks} ({percentage}%) — {understanding}")
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
