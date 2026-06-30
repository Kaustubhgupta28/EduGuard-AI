import streamlit as st
import os
import tempfile
import json
import time

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="EduGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Serif+Display&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background — soft rose white */
.stApp {
    background: #fff5f6;
    color: #3b1219;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* Hero Banner */
.hero {
    background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 50%, #fce7f3 100%);
    border: 1.5px solid #fecdd3;
    border-radius: 20px;
    padding: 44px;
    text-align: center;
    margin-bottom: 32px;
}
.hero h1 {
    font-size: 3rem;
    font-weight: 700;
    background: linear-gradient(90deg, #e11d48, #be123c, #9d174d);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0;
}
.hero p {
    color: #9d174d;
    font-size: 1.05rem;
    margin: 0;
}

/* Step Tracker */
.step-tracker {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0;
    margin-bottom: 36px;
    padding: 20px;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
}
.step-circle {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.95rem;
    border: 2px solid #fecdd3;
    background: #fff1f2;
    color: #fda4af;
    transition: all 0.3s;
}
.step-circle.active {
    background: #e11d48;
    border-color: #fb7185;
    color: white;
    box-shadow: 0 0 20px rgba(225,29,72,0.3);
}
.step-circle.done {
    background: #be123c;
    border-color: #fb7185;
    color: white;
}
.step-label {
    font-size: 0.72rem;
    color: #fda4af;
    margin-top: 8px;
    text-align: center;
    white-space: nowrap;
}
.step-label.active { color: #e11d48; font-weight: 600; }
.step-label.done   { color: #be123c; }
.step-connector {
    width: 60px;
    height: 2px;
    background: #fecdd3;
    margin: 0 4px;
    margin-bottom: 24px;
}
.step-connector.done { background: #fb7185; }

/* Cards */
.card {
    background: #ffffff;
    border: 1.5px solid #fecdd3;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
}
.card-title {
    font-size: 1rem;
    font-weight: 600;
    color: #be123c;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Score Badges */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-green  { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef9c3; color: #854d0e; }
.badge-red    { background: #fff1f2; color: #be123c; }
.badge-blue   { background: #fce7f3; color: #9d174d; }

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}
.metric-card {
    background: #fff1f2;
    border: 1px solid #fecdd3;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #e11d48;
    font-family: 'Inter', monospace;
}
.metric-label {
    font-size: 0.75rem;
    color: #9d174d;
    margin-top: 4px;
}

/* Viva Question Box */
.viva-box {
    background: #ffffff;
    border: 1.5px solid #fecdd3;
    border-left: 5px solid #e11d48;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 16px;
}
.viva-level {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.level-basic        { color: #16a34a; }
.level-intermediate { color: #d97706; }
.level-advanced     { color: #e11d48; }
.viva-question {
    font-size: 1rem;
    color: #3b1219;
    line-height: 1.6;
}

/* Day Roadmap */
.day-card {
    background: #ffffff;
    border: 1px solid #fecdd3;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.day-number {
    background: #e11d48;
    color: white;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    flex-shrink: 0;
}
.day-content { flex: 1; }
.day-topic { font-weight: 600; color: #3b1219; margin-bottom: 4px; }
.day-goal  { font-size: 0.82rem; color: #9d174d; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #e11d48, #be123c) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(79,70,229,0.4) !important;
}
.stButton > button:disabled,
.stButton > button[disabled] {
    background: #fecdd3 !important;
    color: #fda4af !important;
    cursor: not-allowed !important;
    box-shadow: none !important;
    opacity: 0.7 !important;
}
.stButton > button:disabled:hover,
.stButton > button[disabled]:hover {
    transform: none !important;
    box-shadow: none !important;
}

/* Radio button — no pre-filled circle styling */
.stRadio [role="radiogroup"] label {
    background: #fff1f2 !important;
    border: 1.5px solid #fecdd3 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
    transition: all 0.2s !important;
}
.stRadio [role="radiogroup"] label:hover {
    border-color: #fb7185 !important;
    background: #ffe4e6 !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #fff1f2 !important;
    border: 2px dashed #fda4af !important;
    border-radius: 12px !important;
}

/* Text input */
.stTextArea textarea {
    background: #ffffff !important;
    border: 1.5px solid #fecdd3 !important;
    color: #3b1219 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextArea textarea:focus {
    border-color: #e11d48 !important;
    box-shadow: 0 0 0 2px rgba(225,29,72,0.15) !important;
}

/* Radio buttons */
.stRadio label {
    color: #3b1219 !important;
    font-size: 0.95rem !important;
}
.stRadio [data-testid="stRadio"] {
    background: #fff1f2 !important;
    border-radius: 10px !important;
    padding: 12px !important;
    border: 1px solid #fecdd3 !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #e11d48, #fb7185) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #fff1f2 !important;
    border: 1px solid #fecdd3 !important;
    border-radius: 10px !important;
    padding: 12px !important;
}
[data-testid="stMetricLabel"] { color: #9d174d !important; }
[data-testid="stMetricValue"] { color: #be123c !important; }

/* Info/Success/Warning boxes */
.stAlert { border-radius: 10px !important; }
.stSuccess { background: #f0fdf4 !important; border-color: #86efac !important; }
.stInfo    { background: #fff1f2 !important; border-color: #fecdd3 !important; }
.stWarning { background: #fefce8 !important; border-color: #fde047 !important; }

/* Spinner */
.stSpinner > div { border-top-color: #e11d48 !important; }

/* Selectbox & inputs */
.stSelectbox select, .stTextInput input {
    border: 1.5px solid #fecdd3 !important;
    border-radius: 8px !important;
    color: #3b1219 !important;
}

/* Divider */
hr { border-color: #fecdd3 !important; }

/* Download button */
.stDownloadButton > button {
    background: #fff1f2 !important;
    color: #be123c !important;
    border: 1.5px solid #fda4af !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: #fecdd3 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "file_path": None,
        "groq_api_key": None,
        "doc_profile": None,
        "ai_detection": None,
        "raw_text": None,
        "questions": None,
        "answers": {},
        "current_q": 0,
        "viva_results": None,
        "feedback": None,
        "study_roadmap": None,
        "temp_file": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Hero ──────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🛡️ EduGuard AI</h1>
    <p>Agentic Academic Integrity Framework &nbsp;·&nbsp; Evaluating Understanding, Not Just Output</p>
</div>
""", unsafe_allow_html=True)


# ── Step Tracker ──────────────────────────────────────────────
def step_tracker(current):
    steps = ["Upload", "Analysis", "Viva", "Feedback", "Roadmap"]
    html = '<div class="step-tracker">'
    for i, label in enumerate(steps, 1):
        if i < current:
            circle_cls = "done"
            label_cls  = "done"
            icon = "✓"
        elif i == current:
            circle_cls = "active"
            label_cls  = "active"
            icon = str(i)
        else:
            circle_cls = ""
            label_cls  = ""
            icon = str(i)

        html += f'<div class="step-item"><div class="step-circle {circle_cls}">{icon}</div><div class="step-label {label_cls}">{label}</div></div>'

        if i < len(steps):
            conn_cls = "done" if i < current else ""
            html += f'<div class="step-connector {conn_cls}"></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

step_tracker(st.session_state.step)


# ── Helper: badge ─────────────────────────────────────────────
def badge(text, color="blue"):
    return f'<span class="badge badge-{color}">{text}</span>'


# ════════════════════════════════════════════════════════════
#  STEP 1 — Upload
# ════════════════════════════════════════════════════════════

# ── Auto-load API key from Streamlit secrets or .env ──
def get_api_key():
    # Priority 1: Streamlit Cloud secrets
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    # Priority 2: .env / environment variable
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    key = os.getenv("GROQ_API_KEY", None)
    if key:
        return key
    return None

auto_key = get_api_key()

if st.session_state.step == 1:
    st.markdown("### 📁 Step 1 — Upload Submission")
    st.markdown('<p style="color:#64748b">Upload any student submission file to begin evaluation.</p>', unsafe_allow_html=True)

    if auto_key:
        # Key found automatically — full width uploader
        st.markdown('<div style="background:#064e3b;border:1px solid #34d399;border-radius:8px;padding:10px 16px;margin-bottom:16px;color:#34d399;font-size:0.85rem">✅ API Key loaded automatically — no need to enter manually.</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drop your file here",
            type=["pdf", "docx", "pptx", "txt", "py", "js", "java", "cpp"],
            label_visibility="collapsed"
        )
        api_key = auto_key
    else:
        # No key found — show input box
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded = st.file_uploader(
                "Drop your file here",
                type=["pdf", "docx", "pptx", "txt", "py", "js", "java", "cpp"],
                label_visibility="collapsed"
            )
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">🔑 Groq API Key</div>', unsafe_allow_html=True)
            api_key = st.text_input("API Key", type="password", placeholder="gsk_...", label_visibility="collapsed")
            st.markdown('<p style="color:#475569;font-size:0.75rem">Get free key at console.groq.com</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📋 Supported Formats</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for col, fmt in zip(cols, ["📄 PDF", "📝 DOCX", "📊 PPTX", "💻 Code"]):
        col.markdown(f'<p style="color:#94a3b8;text-align:center">{fmt}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded and api_key:
        if st.button("🚀 Start Evaluation", use_container_width=True):
            suffix = os.path.splitext(uploaded.name)[1]
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uploaded.read())
            tmp.close()

            st.session_state.temp_file    = tmp.name
            st.session_state.file_path    = tmp.name
            st.session_state.groq_api_key = api_key
            st.session_state.step         = 2
            st.rerun()
    elif uploaded and not api_key:
        st.warning("Please enter your Groq API Key to continue.")
    elif not uploaded:
        st.info("Upload a file to begin.")


# ════════════════════════════════════════════════════════════
#  STEP 2 — Analysis
# ════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown("### 🔍 Step 2 — Submission Analysis")

    if st.session_state.doc_profile is None:
        with st.spinner("Agents are analyzing your submission..."):
            try:
                from agents.submission_agent import run_submission_agent
                from agents.ai_detection_agent import run_ai_detection_agent

                state = {
                    "file_path": st.session_state.file_path,
                    "groq_api_key": st.session_state.groq_api_key,
                }

                # Run submission agent
                state = run_submission_agent(state)
                st.session_state.doc_profile = state.get("doc_profile", {})
                st.session_state.raw_text    = state.get("raw_text", "")

                # Run AI detection agent
                state = run_ai_detection_agent(state)
                st.session_state.ai_detection = state.get("ai_detection", {})

            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

    doc  = st.session_state.doc_profile
    ai   = st.session_state.ai_detection

    # Document Profile
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">📄 Submission Agent — Document Profile</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(f"**Topic:** {doc.get('topic','N/A')}")
    c1.markdown(f"**Subject:** {doc.get('subject_area','N/A')}")
    c1.markdown(f"**Level:** {doc.get('academic_level','N/A')}")
    c2.markdown(f"**Key Concepts:** {', '.join(doc.get('key_concepts',[]))}")
    c2.markdown(f"**Has Math:** {'✅' if doc.get('has_math') else '❌'}  &nbsp; **Has Code:** {'✅' if doc.get('has_code') else '❌'}  &nbsp; **References:** {'✅' if doc.get('has_references') else '❌'}")
    st.markdown(f"**Summary:** {doc.get('summary','N/A')}")
    st.markdown('</div>', unsafe_allow_html=True)

    # AI Detection
    ai_score = ai.get("ai_involvement_score", 0)
    risk     = ai.get("risk_level", "Low")
    color    = {"Low": "green", "Medium": "yellow", "High": "red"}.get(risk, "blue")
    semantic = ai.get("semantic_analysis", {})

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🤖 AI Detection Agent — Writing Analysis</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AI Involvement", f"{ai_score}%")
    m2.metric("Risk Level", risk)
    m3.metric("Burstiness", ai.get("burstiness_score", 0))
    m4.metric("Uniformity", ai.get("uniformity_score", 0))

    st.markdown(f"**Writing Style:** {semantic.get('writing_style','N/A')} &nbsp;|&nbsp; **Vocabulary:** {semantic.get('vocabulary_complexity','N/A')} &nbsp;|&nbsp; **Citations:** {semantic.get('citation_authenticity','N/A')}")

    if semantic.get("red_flags"):
        st.markdown(f"**⚠️ Red Flags:** {', '.join(semantic['red_flags'])}")

    st.markdown(f"**Assessment:** {semantic.get('overall_assessment','N/A')}")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("▶️ Start Viva Session", use_container_width=True):
        st.session_state.step = 3
        st.rerun()


# ════════════════════════════════════════════════════════════
#  STEP 3 — Viva (MCQ + Short Answer)
# ════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown("### 🧠 Step 3 — Knowledge Verification (Viva)")

    # Generate questions once per session
    if st.session_state.questions is None:
        with st.spinner("🎲 Generating unique questions for this session..."):
            try:
                from agents.verification_agent import generate_viva_questions
                qs = generate_viva_questions(
                    st.session_state.doc_profile,
                    st.session_state.raw_text,
                    st.session_state.groq_api_key
                )
                st.session_state.questions = qs
                st.session_state.current_q = 0
                st.session_state.answers   = {}
            except Exception as e:
                st.error(f"Question generation failed: {e}")
                st.stop()

    questions = st.session_state.questions
    current_q = st.session_state.current_q
    total_q   = len(questions)

    # Progress bar
    progress = current_q / total_q if total_q > 0 else 0
    st.progress(progress)
    st.markdown(f'<p style="color:#64748b;text-align:right;font-size:0.85rem">Question {min(current_q+1, total_q)} of {total_q}</p>', unsafe_allow_html=True)

    if current_q < total_q:
        q     = questions[current_q]
        qtype = q.get("type", "mcq")
        level = q.get("level", "Basic")
        marks = q.get("marks", 1)

        level_class = {"Basic": "level-basic", "Intermediate": "level-intermediate", "Advanced": "level-advanced"}.get(level, "level-basic")

        st.markdown(f"""
        <div class="viva-box">
            <div class="viva-level {level_class}">Q{current_q+1} · {level} · {marks} mark{"s" if marks > 1 else ""} · {"MCQ" if qtype == "mcq" else "Short Answer"}</div>
            <div class="viva-question">{q.get("question", "")}</div>
        </div>
        """, unsafe_allow_html=True)

        if qtype == "mcq":
            options = q.get("options", {})
            option_labels = [f"{k}) {v}" for k, v in options.items()]
            selected = st.radio(
                "Choose your answer:",
                option_labels,
                index=None,
                key=f"mcq_{current_q}",
                label_visibility="collapsed"
            )
            is_disabled = selected is None
            if st.button("Submit ▶️", use_container_width=True, key=f"sub_{current_q}", disabled=is_disabled):
                chosen_letter = selected[0] if selected else ""
                st.session_state.answers[current_q] = chosen_letter
                st.session_state.current_q += 1
                st.rerun()
        else:
            # Short answer
            answer = st.text_area(
                "Your Answer (1-2 sentences)",
                height=100,
                placeholder="Write a concise answer...",
                key=f"short_{current_q}",
                label_visibility="collapsed"
            )
            answer_empty = not answer.strip()
            if st.button("Submit ▶️", use_container_width=True, key=f"sub_{current_q}", disabled=answer_empty):
                st.session_state.answers[current_q] = answer.strip()
                st.session_state.current_q += 1
                st.rerun()

    else:
        # All answered — evaluate
        st.success("✅ All questions answered! Evaluating your responses...")

        if st.session_state.viva_results is None:
            with st.spinner("Evaluating answers..."):
                try:
                    from agents.verification_agent import evaluate_mcq, evaluate_short_answer
                    results       = []
                    total_score   = 0
                    total_marks   = 0
                    weak_concepts = []

                    for i, q in enumerate(questions):
                        ans   = st.session_state.answers.get(i, "")
                        qtype = q.get("type", "mcq")

                        if qtype == "mcq":
                            ev = evaluate_mcq(q, ans)
                        else:
                            ev = evaluate_short_answer(
                                q["question"], ans,
                                q.get("expected_keywords", []),
                                q.get("marks", 3),
                                st.session_state.groq_api_key
                            )

                        total_score += ev.get("score", 0)
                        total_marks += ev.get("max_marks", q.get("marks", 1))
                        weak_concepts.extend(ev.get("missing_concepts", []))
                        results.append({
                            "question_no": i+1, "level": q.get("level"),
                            "type": qtype, "question": q.get("question"),
                            "student_answer": ans, "evaluation": ev
                        })

                    pct = round((total_score / total_marks) * 100, 1) if total_marks else 0
                    und = "Excellent" if pct >= 80 else "Good" if pct >= 60 else "Moderate" if pct >= 40 else "Poor"

                    st.session_state.viva_results = {
                        "questions_and_answers": results,
                        "total_score": total_score,
                        "total_marks": total_marks,
                        "percentage": pct,
                        "understanding_level": und,
                        "weak_concepts": list(set(weak_concepts)),
                    }
                except Exception as e:
                    st.error(f"Evaluation failed: {e}")
                    st.stop()

        viva = st.session_state.viva_results
        pct  = viva.get("percentage", 0)
        und  = viva.get("understanding_level", "")

        # Show results with answer review
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📊 Viva Results</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Score", f"{viva['total_score']}/{viva['total_marks']}")
        c2.metric("Percentage",  f"{pct}%")
        c3.metric("Understanding", und)
        if viva.get("weak_concepts"):
            st.markdown(f"**Weak Areas:** {', '.join(viva['weak_concepts'])}")
        st.markdown('</div>', unsafe_allow_html=True)

        # MCQ answer review
        st.markdown("**📋 Answer Review:**")
        for r in viva.get("questions_and_answers", []):
            ev = r.get("evaluation", {})
            is_correct = ev.get("is_correct", None)
            icon = "✅" if is_correct else ("❌" if is_correct is False else "📝")
            qtype = r.get("type", "mcq")
            if qtype == "mcq":
                st.markdown(f"{icon} **Q{r['question_no']}** [{r['level']}] — Selected: **{r['student_answer']}** | Correct: **{ev.get('correct_option','')}**")
            else:
                st.markdown(f"📝 **Q{r['question_no']}** [Short] — Score: {ev.get('score',0)}/{ev.get('max_marks',3)}")

        if st.button("▶️ Get Feedback & Roadmap", use_container_width=True):
            st.session_state.step = 4
            st.rerun()


# ════════════════════════════════════════════════════════════
#  STEP 4 — Feedback
# ════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    st.markdown("### 💬 Step 4 — Personalized Feedback")

    if st.session_state.feedback is None:
        with st.spinner("Feedback Agent is generating your report..."):
            try:
                from agents.feedback_agent import run_feedback_agent
                state = {
                    "doc_profile":  st.session_state.doc_profile,
                    "viva_results": st.session_state.viva_results,
                    "ai_detection": st.session_state.ai_detection,
                    "groq_api_key": st.session_state.groq_api_key,
                }
                state = run_feedback_agent(state)
                st.session_state.feedback = state.get("feedback", {})
            except Exception as e:
                st.error(f"Feedback generation failed: {e}")
                st.stop()

    fb   = st.session_state.feedback
    sfb  = fb.get("student_feedback", {})
    prof = fb.get("professor_report", {})

    # Student Feedback
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🎓 Student Feedback</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#e2e8f0">{sfb.get("overall_message","")}</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**✅ Strengths**")
        for s in sfb.get("strengths", []):
            st.markdown(f"- {s}")
    with c2:
        st.markdown("**📈 Areas to Improve**")
        for a in sfb.get("areas_to_improve", []):
            st.markdown(f"- {a}")
    st.markdown(f'**⚡ Action:** {sfb.get("immediate_action","")}')
    st.markdown(f'<p style="color:#818cf8;font-style:italic">{sfb.get("encouragement","")}</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Professor Report
    rec   = prof.get("recommended_action", "")
    rec_color = "green" if rec == "Pass" else "yellow" if "Viva" in rec else "red"
    concern = prof.get("integrity_concern_level", "")
    con_color = {"None": "green", "Low": "green", "Moderate": "yellow", "High": "red"}.get(concern, "blue")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👨‍🏫 Professor Evaluation Report</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#94a3b8">{prof.get("summary","")}</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**Integrity Concern**\n\n{concern}")
    c2.markdown(f"**Recommendation**\n\n{rec}")
    c3.markdown(f"**AI Usage Assessment**\n\n{prof.get('ai_usage_assessment','')[:60]}...")
    st.markdown(f'**Notes:** {prof.get("notes_for_professor","")}')
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("▶️ Generate Study Roadmap", use_container_width=True):
        st.session_state.step = 5
        st.rerun()


# ════════════════════════════════════════════════════════════
#  STEP 5 — Roadmap
# ════════════════════════════════════════════════════════════
elif st.session_state.step == 5:
    st.markdown("### 🗓️ Step 5 — Personalized Study Roadmap")

    if st.session_state.study_roadmap is None:
        with st.spinner("Learning Coach Agent is building your roadmap..."):
            try:
                from agents.coach_agent import run_coach_agent
                state = {
                    "doc_profile":  st.session_state.doc_profile,
                    "viva_results": st.session_state.viva_results,
                    "feedback":     st.session_state.feedback,
                    "groq_api_key": st.session_state.groq_api_key,
                }
                state = run_coach_agent(state)
                st.session_state.study_roadmap = state.get("study_roadmap", {})
            except Exception as e:
                st.error(f"Roadmap generation failed: {e}")
                st.stop()

    roadmap = st.session_state.study_roadmap

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">📚 {roadmap.get("roadmap_title","7-Day Study Plan")}</div>', unsafe_allow_html=True)
    st.markdown(f'**Final Goal:** {roadmap.get("final_milestone","")}', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    for day in roadmap.get("daily_plan", []):
        resources = " · ".join([f"{r['title']} ({r['platform']})" for r in day.get("resources", [])])
        st.markdown(f"""
        <div class="day-card">
            <div class="day-number">D{day['day']}</div>
            <div class="day-content">
                <div class="day-topic">{day.get('focus_topic','')}</div>
                <div class="day-goal">{day.get('goal','')}</div>
                <div style="font-size:0.78rem;color:#475569;margin-top:6px">📚 {resources}</div>
                <div style="font-size:0.78rem;color:#475569;margin-top:4px">✏️ {day.get('practice','')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<p style="color:#818cf8;font-style:italic;text-align:center;margin-top:16px">💬 {roadmap.get("motivational_note","")}</p>', unsafe_allow_html=True)

    st.markdown("---")

    # Final summary metrics
    st.markdown("### 📊 Final Evaluation Summary")
    viva = st.session_state.viva_results or {}
    ai   = st.session_state.ai_detection or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Viva Score",       f"{viva.get('percentage',0)}%")
    c2.metric("Understanding",    viva.get("understanding_level","N/A"))
    c3.metric("AI Involvement",   f"{ai.get('ai_involvement_score',0)}%")
    c4.metric("Risk Level",       ai.get("risk_level","N/A"))

    # Download report
    report_data = {
        "doc_profile":  st.session_state.doc_profile,
        "ai_detection": st.session_state.ai_detection,
        "viva_results": st.session_state.viva_results,
        "feedback":     st.session_state.feedback,
        "study_roadmap": st.session_state.study_roadmap,
    }
    st.download_button(
        "⬇️ Download Full Report (JSON)",
        data=json.dumps(report_data, indent=2),
        file_name="eduguard_report.json",
        mime="application/json",
        use_container_width=True
    )

    if st.button("🔄 Evaluate Another Submission", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()