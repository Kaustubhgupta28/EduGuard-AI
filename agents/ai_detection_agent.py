import math
import re
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


# ─────────────────────────────────────────────
#  Heuristic Scoring (No external API needed)
#  — Used as a supporting signal, not primary
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

    cv = std_dev / mean if mean > 0 else 0
    return min(cv, 1.0)


def compute_uniformity(text: str) -> float:
    """
    Uniformity = how repetitive AI-typical transition/filler phrases are.
    Returns 0.0 (diverse/human) to 1.0 (uniform/AI-like).
    """
    ai_phrases = [
        "furthermore", "moreover", "in addition", "it is important to note",
        "it is worth noting", "in conclusion", "to summarize", "as mentioned",
        "plays a crucial role", "it is essential", "delve into", "leverage",
        "in the realm of", "it should be noted", "one must consider",
        "facilitates", "encompasses", "utilizes", "demonstrates",
        "additionally", "consequently", "in essence", "overall, ",
        "in today's", "in conclusion,", "ultimately", "this highlights",
        "underscores", "showcasing", "comprehensive understanding",
        "plethora of", "myriad of", "navigate the complexities",
        "in summary", "fosters", "enables", "robust", "seamless",
        "synergy", "holistic", "paradigm", "cutting-edge", "innovative solution",
    ]
    text_lower = text.lower()
    total_words = len(text_lower.split())
    if total_words == 0:
        return 0.0

    hit_count = sum(text_lower.count(phrase) for phrase in ai_phrases)
    score = min(hit_count / max(total_words / 60, 1), 1.0)
    return score


def compute_perplexity_proxy(text: str) -> float:
    """
    Proxy perplexity using avg word length and sentence-length consistency.
    Returns 0.0 (predictable/AI) to 1.0 (complex/human).
    """
    words = text.split()
    if not words:
        return 0.5

    avg_word_length = sum(len(w) for w in words) / len(words)
    complexity = min((avg_word_length - 3) / 6, 1.0)
    return max(complexity, 0.0)


def compute_heuristic_score(text: str) -> dict:
    """
    Combine heuristics into a supporting AI-likelihood score (0-100).
    This is intentionally a SECONDARY signal — LLM judgment carries more weight.
    """
    burstiness = compute_burstiness(text)
    uniformity = compute_uniformity(text)
    perplexity = compute_perplexity_proxy(text)

    human_signals = (burstiness * 0.45) + (perplexity * 0.25) + ((1 - uniformity) * 0.30)
    heuristic_ai_score = round((1 - human_signals) * 100, 1)
    heuristic_ai_score = max(0.0, min(100.0, heuristic_ai_score))

    return {
        "heuristic_ai_score": heuristic_ai_score,
        "burstiness_score": round(burstiness, 3),
        "uniformity_score": round(uniformity, 3),
        "perplexity_proxy": round(perplexity, 3),
    }


# ─────────────────────────────────────────────
#  LLM-Based Semantic Analysis (PRIMARY signal)
# ─────────────────────────────────────────────

def llm_ai_analysis(text: str, groq_api_key: str) -> dict:
    """
    Use LLM as the primary judge of AI-generated content.
    LLMs are dramatically better at this than statistical heuristics —
    they can recognize generation patterns, tone, and structure that
    burstiness/perplexity proxies miss entirely.
    """
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.0)

    system_prompt = """You are a world-class expert in detecting AI-generated academic text. You have analyzed thousands of human-written and AI-generated documents and can reliably distinguish them.

Carefully analyze the given text for AI-generation signals:
- Overly polished, uniform sentence structures with no natural imperfection
- Generic transition phrases typical of LLM output (e.g. "Furthermore", "In conclusion", "It is important to note", "This highlights", "plays a crucial role")
- Suspiciously balanced, "textbook-perfect" explanations lacking personal voice, specific detail, or natural digression
- Vague, generic claims without concrete specifics, numbers, or personal examples
- Repetitive sentence openers and paragraph structures
- Absence of typos, informal phrasing, or natural human inconsistency
- Hedge-free, overly confident tone throughout
- Content that reads like a summary/encyclopedia entry rather than a student's own reasoning process

Be DECISIVE. If text shows multiple AI-generation signals, score it high (60-95%). If text shows clear human markers (specific personal examples, minor inconsistencies, informal asides, unique voice, concrete numbers/anecdotes), score it low (5-30%). Do not default to the middle — most text is NOT ambiguous once you look carefully.

Return ONLY valid JSON with these exact keys:
{
  "ai_probability_score": <integer 0-100, your confident estimate of % likelihood this was AI-generated>,
  "writing_style": "Natural/Structured/Overly-Formal/Mixed",
  "vocabulary_complexity": "Simple/Moderate/Complex/Overly-Complex",
  "transition_pattern": "Varied/Repetitive/AI-Typical",
  "citation_authenticity": "Authentic/Suspicious/No-Citations",
  "overall_assessment": "2-3 sentence assessment explaining your reasoning and the specific signals you found",
  "red_flags": ["specific phrase or pattern 1", "specific phrase or pattern 2", "specific phrase or pattern 3"]
}
Return ONLY JSON. No markdown. No explanation outside the JSON."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this text for AI-generation signals (full text below):\n\n{text[:4000]}")
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content.strip())
        # Ensure score is a valid number
        result["ai_probability_score"] = max(0, min(100, float(result.get("ai_probability_score", 50))))
        return result
    except Exception:
        return {
            "ai_probability_score": 50.0,
            "writing_style": "Unknown",
            "vocabulary_complexity": "Unknown",
            "transition_pattern": "Unknown",
            "citation_authenticity": "Unknown",
            "overall_assessment": "Analysis unavailable due to parsing error.",
            "red_flags": []
        }


# ─────────────────────────────────────────────
#  Main Agent Function
# ─────────────────────────────────────────────

def run_ai_detection_agent(state: dict) -> dict:
    """
    AI Detection Agent:
    - Runs LLM semantic analysis (PRIMARY signal — 75% weight)
    - Computes heuristic scores as a supporting signal (25% weight)
    - Produces final, decisive AI Involvement Score
    """
    raw_text     = state.get("raw_text", "")
    groq_api_key = state.get("groq_api_key")

    print("[AI Detection Agent] Analyzing writing patterns...")

    # LLM analysis — primary signal
    semantic = llm_ai_analysis(raw_text, groq_api_key)
    llm_score = semantic.get("ai_probability_score", 50.0)

    # Heuristic analysis — supporting signal
    heuristic = compute_heuristic_score(raw_text)
    heuristic_score = heuristic["heuristic_ai_score"]

    # Weighted final score: LLM judgment dominates
    final_score = round((llm_score * 0.75) + (heuristic_score * 0.25), 1)
    final_score = max(0.0, min(100.0, final_score))

    if final_score < 25:
        label = "Likely Human-Written"
        risk  = "Low"
    elif final_score < 55:
        label = "Mixed AI Assistance"
        risk  = "Medium"
    else:
        label = "Highly AI-Generated"
        risk  = "High"

    print(f"  LLM Score        : {llm_score}%")
    print(f"  Heuristic Score  : {heuristic_score}%")
    print(f"  Final AI Score   : {final_score}%")
    print(f"  Risk Level       : {risk}")
    print(f"  Label            : {label}")
    print("[AI Detection Agent] Done.\n")

    return {
        **state,
        "ai_detection": {
            "ai_involvement_score": final_score,
            "label": label,
            "risk_level": risk,
            "llm_score": llm_score,
            "heuristic_score": heuristic_score,
            "burstiness_score": heuristic["burstiness_score"],
            "uniformity_score": heuristic["uniformity_score"],
            "perplexity_proxy": heuristic["perplexity_proxy"],
            "semantic_analysis": semantic,
        }
    }