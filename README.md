# EduGuard AI 🛡️
### Agentic Academic Integrity Framework

> *"Evaluating Understanding, Not Just Output"*

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LLM-orange?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

---

## 🎯 Problem Statement

Educational institutions lack intelligent systems capable of balancing AI adoption with genuine student learning and academic integrity.

Today students use AI tools for assignments, PPTs, reports, and coding — but professors cannot identify real understanding. Traditional plagiarism tools fail against AI-generated content, and marks no longer reflect actual learning.

**The Core Challenge:**
> *"How can institutions balance AI assistance with genuine student learning?"*

---

## 💡 Solution — EduGuard AI

EduGuard AI is a **Multi-Agent Agentic Framework** that doesn't ban AI — it evaluates whether real learning happened alongside it.

Instead of punishing AI usage, the system:
- 📄 Analyzes student submissions intelligently
- 🔍 Estimates AI involvement using NLP heuristics
- 🧠 Conducts adaptive viva sessions to verify understanding
- 💬 Provides personalized mentor-style feedback
- 🗓️ Generates a step-by-step study roadmap for weak areas
- 👨‍🏫 Produces a complete professor evaluation report

---

## 🏗️ Multi-Agent Architecture

```
Student File Upload (PDF / DOCX / PPTX / Code)
                    │
                    ▼
         ┌─────────────────────┐
         │   Submission Agent  │  ← Extracts text, detects topic & key concepts
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  AI Detection Agent │  ← Perplexity + Burstiness + LLM Semantic Analysis
         └─────────┬───────────┘
                   │
                   ▼
         ┌──────────────────────────┐
         │ Knowledge Verification   │  ← Adaptive Viva (Basic → Intermediate → Advanced)
         │        Agent             │
         └─────────┬────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │    Feedback Agent   │  ← Student feedback + Professor evaluation report
         └─────────┬───────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Learning Coach     │  ← Personalized 7-day study roadmap
         │       Agent         │
         └─────────────────────┘
```

---

## 🤖 Agent Details

| Agent | Role |
|-------|------|
| **Submission Agent** | Reads PDF/DOCX/PPTX/Code files, extracts text, detects topic & key concepts using LLM |
| **AI Detection Agent** | Computes Perplexity, Burstiness & Uniformity scores + LLM semantic writing analysis |
| **Knowledge Verification Agent** | Generates 6 adaptive viva questions (2 Basic, 2 Intermediate, 2 Advanced), evaluates answers |
| **Feedback Agent** | Produces mentor-style student feedback + structured professor evaluation report |
| **Learning Coach Agent** | Builds a personalized 7-day study roadmap targeting weak concepts with resources |

---

## ⚙️ Tech Stack

| Category | Technology |
|----------|------------|
| Agent Framework | LangGraph |
| LLM Backend | Groq API (llama-3.3-70b-versatile) |
| File Processing | PyMuPDF, python-docx, python-pptx |
| NLP Heuristics | Custom Perplexity + Burstiness scoring |
| CLI Interface | Rich (beautiful terminal output) |
| Environment | python-dotenv |

---

## 📁 Project Structure

```
eduguard_ai/
│
├── agents/
│   ├── submission_agent.py       # File reading + topic detection
│   ├── ai_detection_agent.py     # AI involvement scoring
│   ├── verification_agent.py     # Viva Q&A + evaluation
│   ├── feedback_agent.py         # Student + Professor feedback
│   └── coach_agent.py            # 7-day study roadmap
│
├── graph/
│   └── workflow.py               # LangGraph pipeline
│
├── utils/
│   └── file_extractor.py         # PDF/DOCX/PPTX text extraction
│
├── main.py                       # CLI entry point
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Kaustubhgupta28/EduGuard-AI.git
cd EduGuard-AI
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup environment
```bash
cp .env.example .env
```
Add your Groq API key in `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get your free API key at [console.groq.com](https://console.groq.com)

### 4. Run EduGuard AI
```bash
python main.py path/to/your_submission.pdf
```

**Supported formats:** `.pdf` `.docx` `.pptx` `.py` `.js` `.txt`

---

## 📊 Sample Output

```
╭─────────────────────────────────────────╮
│  EduGuard AI                            │
│  Agentic Academic Integrity Framework   │
│  Evaluating Understanding, Not Just     │
│  Output                                 │
╰─────────────────────────────────────────╯

[Submission Agent] Reading and analyzing file...
  Topic    : Introduction to LSTM Networks
  Subject  : Machine Learning
  Concepts : LSTM, vanishing gradient, forget gate, cell state

[AI Detection Agent] Analyzing writing patterns...
  AI Involvement Score : 38.5%
  Risk Level           : Low
  Label                : Likely Human-Written

[Knowledge Verification Agent] Generating viva questions...

  Q1 [Basic] (2 marks)
  What is the primary purpose of LSTM networks?
  Your Answer: _

  ...

FINAL EVALUATION REPORT
┌────────────────────────────┬──────────────┬──────────────────────┐
│ Metric                     │ Score        │ Status               │
├────────────────────────────┼──────────────┼──────────────────────┤
│ AI Involvement             │ 38.5%        │ Likely Human-Written │
│ Viva Score                 │ 82%          │ Good                 │
│ Integrity Concern          │ Low          │                      │
│ Recommendation             │ Pass         │                      │
└────────────────────────────┴──────────────┴──────────────────────┘
```

---

## 🔥 Innovation

Most AI detectors only detect AI-generated text.

**EduGuard AI evaluates learning quality.**

| Traditional Tools | EduGuard AI |
|-------------------|-------------|
| Detects AI text only | Evaluates conceptual understanding |
| Binary pass/fail output | Multi-dimensional scoring |
| No student feedback | Full mentor-style guidance |
| Punishes AI usage | Encourages responsible AI use |
| No improvement path | Personalized 7-day study roadmap |

---

## 🔬 Research Contribution

1. **Novel multi-agent architecture** for academic integrity evaluation
2. **Learning-centric evaluation methodology** — understanding prioritized over originality
3. **Ethical AI adoption framework** for educational institutions

> *"This framework introduces a paradigm shift from content originality checking to conceptual understanding verification."*

---

## 🔮 Future Scope

- 🎙️ Voice-based viva integration
- 🌐 Multilingual support
- 📚 LMS integration (Moodle, Google Classroom)
- 📱 Mobile app for students
- 🔍 Explainable AI — why a submission was flagged
- 📊 Institutional analytics dashboard

---

## 👨‍💻 Author

**Kaustubh Gupta**
B.Tech CSE (AI/ML) — LNCT University, Bhopal

[![GitHub](https://img.shields.io/badge/GitHub-Kaustubhgupta28-black?style=flat-square&logo=github)](https://github.com/Kaustubhgupta28)

---

## 📄 License

This project is licensed under the MIT License.
