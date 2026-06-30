import math
import re
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


# ─────────────────────────────────────────────
#  Content Type Detection
# ─────────────────────────────────────────────

def detect_content_type(text: str) -> str:
    """
    Detect whether the submission is primarily CODE or PROSE.
    Code needs entirely different AI-detection signals than prose —
    AI-typical transition phrases don't appear in code, but AI-generated
    code has its own tells (perfect docstrings, consistent naming,
    no leftover debug prints, textbook comments, zero typos).
    """
    code_signals = [
        r'\bdef\s+\w+\s*\(', r'\bclass\s+\w+', r'\bimport\s+\w+', r'\bfrom\s+\w+\s+import',
        r'\breturn\s+', r'\bif\s+.*:', r'\bfor\s+\w+\s+in\s+', r'\bwhile\s+.*:',
        r'function\s+\w+\s*\(', r'const\s+\w+\s*=', r'let\s+\w+\s*=', r'var\s+\w+\s*=',
        r'public\s+(static\s+)?\w+\s+\w+\s*\(', r'#include\s*<', r'console\.log\(',
        r'\bprint\(', r'st\.\w+\(', r'<\w+[^>]*>.*</\w+>',
    ]
    hits = sum(1 for pattern in code_signals if re.search(pattern, text))
    code_density = hits / max(len(text.split('\n')), 1) * 10

    # If heavy code syntax density, classify as code
    if hits >= 4 or code_density > 1.5:
        return "code"
    return "prose"


# ─────────────────────────────────────────────
#  Heuristic Scoring for PROSE (supporting signal)
# ─────────────────────────────────────────────

def compute_burstiness(text: str) -> float:
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
    ai_phrases = [
        "furthermore", "moreover", "in addition", "it is important to note",
        "it is worth noting", "in conclusion", "to summarize", "as mentioned",
        "plays a crucial role", "it is essential", "delve into", "leverage",
        "in the realm of", "it should be noted", "one must consider",
        "facilitates", "encompasses", "utilizes", "demonstrates",
        "additionally", "consequently", "in essence", "overall, ",
        "in today's", "ultimately", "this highlights", "underscores",
        "showcasing", "comprehensive understanding", "plethora of",
        "myriad of", "navigate the complexities", "in summary", "fosters",
        "enables", "robust", "seamless", "synergy", "holistic", "paradigm",
        "cutting-edge", "innovative solution",
    ]
    text_lower = text.lower()
    total_words = len(text_lower.split())
    if total_words == 0:
        return 0.0
    hit_count = sum(text_lower.count(phrase) for phrase in ai_phrases)
    score = min(hit_count / max(total_words / 60, 1), 1.0)
    return score


def compute_perplexity_proxy(text: str) -> float:
    words = text.split()
    if not words:
        return 0.5
    avg_word_length = sum(len(w) for w in words) / len(words)
    complexity = min((avg_word_length - 3) / 6, 1.0)
    return max(complexity, 0.0)


def compute_prose_heuristic(text: str) -> dict:
    burstiness = compute_burstiness(text)
    uniformity = compute_uniformity(text)
    perplexity = compute_perplexity_proxy(text)
    human_signals = (burstiness * 0.45) + (perplexity * 0.25) + ((1 - uniformity) * 0.30)
    score = round((1 - human_signals) * 100, 1)
    return {
        "heuristic_ai_score": max(0.0, min(100.0, score)),
        "burstiness_score": round(burstiness, 3),
        "uniformity_score": round(uniformity, 3),
        "perplexity_proxy": round(perplexity, 3),
    }


# ─────────────────────────────────────────────
#  Heuristic Scoring for CODE (supporting signal)
# ─────────────────────────────────────────────

def compute_code_heuristic(text: str) -> dict:
    """
    Code-specific AI signals:
    - Docstring density (AI loves perfect docstrings on every function)
    - Comment-to-code ratio and comment "textbook-ness"
    - Naming consistency (AI rarely uses inconsistent/abbreviated names)
    - Absence of debug leftovers, TODOs, commented-out code (humans leave mess)
    """
    lines = text.split('\n')
    total_lines = max(len(lines), 1)

    docstring_count = len(re.findall(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', text))
    func_count = len(re.findall(r'\bdef\s+\w+\s*\(', text))
    docstring_ratio = docstring_count / max(func_count, 1) if func_count > 0 else 0

    comment_lines = len(re.findall(r'^\s*#.*$|^\s*//.*$', text, re.MULTILINE))
    comment_density = comment_lines / total_lines

    messy_signals = len(re.findall(
        r'\bTODO\b|\bFIXME\b|\bXXX\b|^\s*#\s*(print|debug|test)|pass\s*#|^\s*//\s*(TODO|debug)',
        text, re.IGNORECASE | re.MULTILINE
    ))

    # AI code tends toward: high docstring ratio, moderate-high comment density,
    # very low messy signals, highly consistent style
    ai_likelihood = 0.0
    ai_likelihood += min(docstring_ratio, 1.0) * 35       # perfect docstrings everywhere
    ai_likelihood += min(comment_density * 8, 30)         # comment-heavy, explanatory style
    ai_likelihood += 25 if messy_signals == 0 else 0       # zero human mess/TODOs
    ai_likelihood += 10  # baseline structural cleanliness bonus

    ai_likelihood = max(0.0, min(100.0, ai_likelihood))

    return {
        "heuristic_ai_score": round(ai_likelihood, 1),
        "docstring_ratio": round(docstring_ratio, 2),
        "comment_density": round(comment_density, 3),
        "messy_signals_found": messy_signals,
    }


# ─────────────────────────────────────────────
#  LLM-Based Semantic Analysis (PRIMARY signal)
# ─────────────────────────────────────────────

def llm_ai_analysis(text: str, content_type: str, groq_api_key: str) -> dict:
    """
    LLM as primary judge. Prompt branches based on content type since
    AI-generated code and AI-generated prose have completely different tells.
    """
    llm = ChatGroq(api_key=groq_api_key, model="llama-3.3-70b-versatile", temperature=0.0)

    if content_type == "code":
        system_prompt = """You are a world-class expert in detecting AI-generated code (e.g. from ChatGPT, Claude, Copilot). You have reviewed thousands of human-written and AI-generated codebases.

Look for AI-CODE-GENERATION signals:
- Perfectly formatted docstrings on EVERY function, written in a uniform textbook style
- Comments that explain the obvious ("# Loop through items") rather than explaining WHY (human comments tend to explain reasoning, edge cases, or workarounds)
- Suspiciously consistent naming conventions throughout with zero abbreviations or inconsistencies
- No leftover debug prints, no commented-out old code, no TODO/FIXME markers (humans almost always leave some mess)
- Overly defensive code (try/except everywhere, validates everything) even for a simple script
- Section header comments like "# ── Step 1 ──" or banner-style comments dividing logical sections
- Code that looks like a tutorial/reference implementation rather than something iteratively hacked together
- Every function has a docstring, type hints are used consistently, error handling is uniformly thorough
- Variable names are textbook-perfect (e.g. "user_input", "result_data") rather than human shorthand (e.g. "tmp", "x2", "data2")

Look for HUMAN-CODE signals:
- Inconsistent style (some functions documented, some not)
- Leftover print() debug statements or commented-out code
- Quick/sloppy variable names, abbreviations
- TODO comments, FIXME, hacky workarounds with comments like "this is gross but works"
- Inconsistent indentation style or mixed conventions
- Missing error handling in some places but present in others (organic, not uniform)

Be DECISIVE. If you see multiple AI-code signals (uniform docstrings, banner comments, zero mess, textbook naming), score HIGH (65-95%). If you see clear human messiness, score LOW (5-25%). Most AI-assisted code, when given to you raw with no edits, shows STRONG signals — don't hedge to the middle.

Return ONLY valid JSON:
{
  "ai_probability_score": <integer 0-100>,
  "writing_style": "Natural/Structured/Overly-Formal/Mixed",
  "vocabulary_complexity": "Simple/Moderate/Complex/Overly-Complex",
  "transition_pattern": "Varied/Repetitive/AI-Typical",
  "citation_authenticity": "Authentic/Suspicious/No-Citations",
  "overall_assessment": "2-3 sentence assessment citing the SPECIFIC code patterns you observed (docstring style, comment style, naming, structure)",
  "red_flags": ["specific pattern 1", "specific pattern 2", "specific pattern 3"]
}
Return ONLY JSON. No markdown."""
    else:
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

    label = "code" if content_type == "code" else "text"
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Analyze this {label} for AI-generation signals (full content below):\n\n{text[:5000]}")
    ])

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content.strip())
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
    - Detects whether submission is code or prose
    - Runs LLM semantic analysis branched by content type (PRIMARY — 75% weight)
    - Computes type-appropriate heuristic score (supporting — 25% weight)
    - Produces final, decisive AI Involvement Score
    """
    raw_text     = state.get("raw_text", "")
    groq_api_key = state.get("groq_api_key")

    print("[AI Detection Agent] Analyzing writing patterns...")

    content_type = detect_content_type(raw_text)
    print(f"  Content Type     : {content_type}")

    # LLM analysis — primary signal, prompt branches on content type
    semantic = llm_ai_analysis(raw_text, content_type, groq_api_key)
    llm_score = semantic.get("ai_probability_score", 50.0)

    # Heuristic analysis — supporting signal, type-appropriate
    if content_type == "code":
        heuristic = compute_code_heuristic(raw_text)
    else:
        heuristic = compute_prose_heuristic(raw_text)
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
            "content_type": content_type,
            "llm_score": llm_score,
            "heuristic_score": heuristic_score,
            **{k: v for k, v in heuristic.items() if k != "heuristic_ai_score"},
            "semantic_analysis": semantic,
        }
    }