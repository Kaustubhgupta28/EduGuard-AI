from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from utils.file_extractor import extract_text


def run_submission_agent(state: dict) -> dict:
    """
    Submission Agent:
    - Reads the uploaded file
    - Extracts text
    - Detects topic, sections, and document profile
    - Passes enriched state forward
    """

    file_path = state.get("file_path")
    groq_api_key = state.get("groq_api_key")

    print("\n[Submission Agent] Reading and analyzing file...")

    # --- Step 1: Extract raw text ---
    file_data = extract_text(file_path)
    raw_text = file_data["raw_text"]

    if not raw_text:
        return {**state, "error": "Could not extract any text from the file."}

    print(f"  File     : {file_data['file_name']}")
    print(f"  Type     : {file_data['file_type']}")
    print(f"  Words    : {file_data['word_count']}")

    # --- Step 2: Use LLM to analyze document ---
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.3)

    system_prompt = """You are an expert academic document analyzer.
Analyze the given student submission and return a structured JSON profile.

Return ONLY valid JSON with these exact keys:
{
  "topic": "main subject/title of the submission",
  "subject_area": "e.g. Machine Learning, Web Development, Networks, etc.",
  "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
  "detected_sections": ["Introduction", "Methodology", ...],
  "academic_level": "Beginner / Intermediate / Advanced",
  "has_code": true/false,
  "has_math": true/false,
  "has_references": true/false,
  "summary": "2-3 sentence summary of the submission"
}

Return ONLY JSON. No explanation. No markdown. No backticks."""

    user_prompt = f"""Analyze this student submission (first 3000 chars):

{raw_text[:3000]}"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    import json
    try:
        doc_profile = json.loads(response.content.strip())
    except Exception:
        # Fallback if JSON parsing fails
        doc_profile = {
            "topic": "Unknown Topic",
            "subject_area": "General",
            "key_concepts": [],
            "detected_sections": [],
            "academic_level": "Intermediate",
            "has_code": False,
            "has_math": False,
            "has_references": False,
            "summary": raw_text[:300]
        }

    print(f"  Topic    : {doc_profile.get('topic')}")
    print(f"  Subject  : {doc_profile.get('subject_area')}")
    print(f"  Concepts : {', '.join(doc_profile.get('key_concepts', []))}")
    print("[Submission Agent] Done.\n")

    return {
        **state,
        "file_data": file_data,
        "raw_text": raw_text,
        "doc_profile": doc_profile,
    }