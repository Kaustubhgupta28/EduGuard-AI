import math
import re
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


# ─────────────────────────────────────────────
#  Heuristic Scoring (No external API needed)
# ─────────────────────────────────────────────

def compute_burstiness(text: str) -> float:
    """
    Burstiness = variation in sentence lengths.
    AI text → very uniform sentence lengths → low burstiness.
    Human text → high variation → high burstiness.
    Returns 0.0 (low/AI-like) to 1.0 (high/human-like).
    """
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if len(sentences) < 3:
        return 0.5

    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std_dev = math.sqrt(variance)

    # Coefficient of variation — normalized
    cv = std_dev / mean if mean > 0 else 0
    # Clamp to 0–1
    return min(cv, 1.0)


def compute_uniformity(text: str) -> float:
    """
    Uniformity = how repetitive the transition words are.
    AI text uses: 'Furthermore', 'Moreover', 'In addition', 'It is important to note'
    Returns 0.0 (diverse/human) to 1.0 (uniform/AI-like).
    """
    ai_phrases = [
        "furthermore", "moreover", "in addition", "it is important to note",
        "it is worth noting", "in conclusion", "to summarize", "as mentioned",
        "plays a crucial role", "it is essential", "delve into", "leverage",
        "in the realm of", "it should be noted", "one must consider",
        "facilitates", "encompasses", "utilizes", "demonstrates"
    ]
    text_lower = text.lower()
    total_words = len(text_lower.split())
    if total_words == 0:
        return 0.0

    hit_count = sum(text_lower.count(phrase) for phrase in ai_phrases)
    # Normalize: more than 1 AI phrase per 100 words → high uniformity
    score = min(hit_count / (total_words / 100), 1.0)
    return score


def compute_perplexity_proxy(text: str) -> float:
    """
    Proxy perplexity using avg word length and sentence complexity.
    AI text tends to have very 'clean' predictable vocabulary.
    Returns 0.0 (predictable/AI) to 1.0 (complex/human).
    """
    words = text.split()
    if not words:
        return 0.5

    avg_word_length = sum(len(w) for w in words) / len(words)
    # Long avg word length = more complex vocabulary
    # Normalize around typical range 4–7 chars
    complexity = min((avg_word_length - 3) / 6, 1.0)
    return max(complexity, 0.0)


def compute_ai_score(text: str) -> dict:
    """
    Combine all heuristics into a final AI Involvement Score (0–100%).
    """
    burstiness   = compute_burstiness(text)      # High = human
    uniformity   = compute_uniformity(text)      # High = AI
    perplexity   = compute_perplexity_proxy(text) # High = human

    # AI score: low burstiness + high uniformity + low perplexity → more AI
    human_signals = (burstiness * 0.4) + (perplexity * 0.3) + ((1 - uniformity) * 0.3)
    ai_involvement = round((1 - human_signals) * 100, 1)
    ai_involvement = max(0.0, min(100.0, ai_involvement))

    if ai_involvement < 30:
        label = "Likely Human-Written"
        risk  = "Low"
    elif ai_involvement < 60:
        label = "Mixed AI Assistance"
        risk  = "Medium"
    else:
        label = "Highly AI-Generated"
        risk  = "High"

    return {
        "ai_involvement_score": ai_involvement,
        "label": label,
        "risk_level": risk,
        "burstiness_score": round(burstiness, 3),
        "uniformity_score": round(uniformity, 3),
        "perplexity_proxy": round(perplexity, 3),
    }


# ─────────────────────────────────────────────
#  LLM-Based Semantic Analysis
# ─────────────────────────────────────────────

def llm_ai_analysis(text: str, groq_api_key: str) -> dict:
    """Use LLM to semantically analyze writing style for AI patterns."""
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.1)

    system_prompt = """You are an expert in identifying AI-generated academic text.
Analyze the given text and return ONLY valid JSON with these keys:
{
  "writing_style": "Natural/Structured/Overly-Formal/Mixed",
  "vocabulary_complexity": "Simple/Moderate/Complex/Overly-Complex",
  "transition_pattern": "Varied/Repetitive/AI-Typical",
  "citation_authenticity": "Authentic/Suspicious/No-Citations",
  "overall_assessment": "1-2 sentence assessment",
  "red_flags": ["flag1", "flag2"]
}
Return ONLY JSON. No markdown. No explanation."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this text (first 2000 chars):\n\n{text[:2000]}")
    ])

    import json
    try:
        return json.loads(response.content.strip())
    except Exception:
        return {
            "writing_style": "Unknown",
            "vocabulary_complexity": "Unknown",
            "transition_pattern": "Unknown",
            "citation_authenticity": "Unknown",
            "overall_assessment": "Analysis unavailable.",
            "red_flags": []
        }


# ─────────────────────────────────────────────
#  Main Agent Function
# ─────────────────────────────────────────────

def run_ai_detection_agent(state: dict) -> dict:
    """
    AI Detection Agent:
    - Computes heuristic scores (burstiness, uniformity, perplexity)
    - Runs LLM semantic analysis
    - Produces final AI Involvement Score
    """
    raw_text     = state.get("raw_text", "")
    groq_api_key = state.get("groq_api_key")

    print("[AI Detection Agent] Analyzing writing patterns...")

    # Heuristic scores
    heuristic = compute_ai_score(raw_text)

    # LLM semantic analysis
    semantic = llm_ai_analysis(raw_text, groq_api_key)

    ai_score = heuristic["ai_involvement_score"]
    print(f"  AI Involvement Score : {ai_score}%")
    print(f"  Risk Level           : {heuristic['risk_level']}")
    print(f"  Label                : {heuristic['label']}")
    print(f"  Writing Style        : {semantic.get('writing_style')}")
    print("[AI Detection Agent] Done.\n")

    return {
        **state,
        "ai_detection": {
            **heuristic,
            "semantic_analysis": semantic,
        }
    }
