"""
EduGuard AI — PDF Report Generator
Converts the full evaluation (doc_profile, ai_detection, viva_results,
feedback, study_roadmap) into a polished, professional PDF report.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)


# ── Rose Petal Palette ──────────────────────────────────────────
ROSE_DARK   = HexColor("#881337")
ROSE        = HexColor("#e11d48")
ROSE_MID    = HexColor("#be123c")
ROSE_LIGHT  = HexColor("#fecdd3")
ROSE_BG     = HexColor("#fff1f2")
TEXT_DARK   = HexColor("#3b1219")
TEXT_MUTED  = HexColor("#9d174d")
GREEN       = HexColor("#16a34a")
GREEN_BG    = HexColor("#dcfce7")
AMBER       = HexColor("#d97706")
AMBER_BG    = HexColor("#fef9c3")
RED         = HexColor("#be123c")
RED_BG      = HexColor("#fff1f2")
WHITE       = HexColor("#ffffff")


def _styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["Title"] = ParagraphStyle(
        "ReportTitle", parent=base["Title"],
        fontName="Helvetica-Bold", fontSize=26, leading=30,
        textColor=ROSE, alignment=TA_CENTER, spaceAfter=4,
    )
    styles["Subtitle"] = ParagraphStyle(
        "Subtitle", parent=base["Normal"],
        fontName="Helvetica", fontSize=11, leading=14,
        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=2,
    )
    styles["Meta"] = ParagraphStyle(
        "Meta", parent=base["Normal"],
        fontName="Helvetica", fontSize=9, leading=12,
        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceAfter=14,
    )
    styles["SectionHeading"] = ParagraphStyle(
        "SectionHeading", parent=base["Heading1"],
        fontName="Helvetica-Bold", fontSize=14, leading=18,
        textColor=ROSE_DARK, spaceBefore=18, spaceAfter=8,
    )
    styles["SubHeading"] = ParagraphStyle(
        "SubHeading", parent=base["Heading2"],
        fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=ROSE_MID, spaceBefore=10, spaceAfter=4,
    )
    styles["Body"] = ParagraphStyle(
        "Body", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=TEXT_DARK, spaceAfter=6,
    )
    styles["BodyMuted"] = ParagraphStyle(
        "BodyMuted", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=9.5, leading=14,
        textColor=TEXT_MUTED, spaceAfter=6,
    )
    styles["Bullet"] = ParagraphStyle(
        "Bullet", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=TEXT_DARK, leftIndent=14, spaceAfter=3,
        bulletIndent=4,
    )
    styles["QuestionLabel"] = ParagraphStyle(
        "QuestionLabel", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9.5, leading=12,
        textColor=ROSE_MID, spaceAfter=2,
    )
    styles["QuestionText"] = ParagraphStyle(
        "QuestionText", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10.5, leading=14,
        textColor=TEXT_DARK, spaceAfter=4,
    )
    styles["AnswerText"] = ParagraphStyle(
        "AnswerText", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=13,
        textColor=TEXT_DARK, spaceAfter=2,
    )
    styles["FeedbackText"] = ParagraphStyle(
        "FeedbackText", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=9, leading=13,
        textColor=TEXT_MUTED, spaceAfter=8,
    )
    styles["DayTitle"] = ParagraphStyle(
        "DayTitle", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10, leading=13,
        textColor=ROSE_DARK,
    )
    styles["DayBody"] = ParagraphStyle(
        "DayBody", parent=base["Normal"],
        fontName="Helvetica", fontSize=9, leading=13,
        textColor=TEXT_DARK, spaceAfter=2,
    )
    styles["Footer"] = ParagraphStyle(
        "Footer", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=8, leading=11,
        textColor=TEXT_MUTED, alignment=TA_CENTER,
    )
    return styles


def _status_chip(text, kind="blue"):
    """Returns an HTML-style colored chip for use inside Paragraphs."""
    colors = {
        "green":  ("#dcfce7", "#166534"),
        "amber":  ("#fef9c3", "#854d0e"),
        "red":    ("#fff1f2", "#be123c"),
        "blue":   ("#fce7f3", "#9d174d"),
    }
    bg, fg = colors.get(kind, colors["blue"])
    return f'<font color="{fg}" backColor="{bg}"> &nbsp;{text}&nbsp; </font>'


def _risk_kind(level):
    return {"Low": "green", "Medium": "amber", "High": "red"}.get(level, "blue")


def _understanding_kind(level):
    return {"Excellent": "green", "Good": "blue", "Moderate": "amber", "Poor": "red"}.get(level, "blue")


def _metric_table(rows, styles, col_widths=None):
    """rows: list of (label, value) tuples → 2-col styled table."""
    data = [[Paragraph(f"<b>{label}</b>", styles["Body"]), Paragraph(value, styles["Body"])] for label, value in rows]
    t = Table(data, colWidths=col_widths or [55*mm, 110*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ROSE_BG),
        ("BOX", (0, 0), (-1, -1), 0.75, ROSE_LIGHT),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, ROSE_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _score_table(viva, styles):
    pct = viva.get("percentage", 0)
    und = viva.get("understanding_level", "N/A")
    rows = [
        ("Total Score", f"{viva.get('total_score',0)} / {viva.get('total_marks',0)}"),
        ("Percentage", f"{pct}%"),
        ("Understanding Level", f'{und} {_status_chip(und, _understanding_kind(und))}'),
    ]
    weak = viva.get("weak_concepts", [])
    if weak:
        rows.append(("Weak Areas", ", ".join(weak)))
    return _metric_table(rows, styles)


def _ai_table(ai, styles):
    score = ai.get("ai_involvement_score", 0)
    risk  = ai.get("risk_level", "N/A")
    label = ai.get("label", "N/A")
    semantic = ai.get("semantic_analysis", {})
    rows = [
        ("AI Involvement Score", f"{score}%"),
        ("Risk Level", f'{risk} {_status_chip(risk, _risk_kind(risk))}'),
        ("Classification", label),
        ("Writing Style", semantic.get("writing_style", "N/A")),
        ("Vocabulary Complexity", semantic.get("vocabulary_complexity", "N/A")),
        ("Citation Authenticity", semantic.get("citation_authenticity", "N/A")),
    ]
    if semantic.get("red_flags"):
        rows.append(("Red Flags", ", ".join(semantic["red_flags"])))
    return _metric_table(rows, styles)


def generate_pdf_report(report_data: dict, student_name: str = None, file_name: str = None) -> bytes:
    """
    Build a polished PDF evaluation report from EduGuard AI pipeline output.
    Returns the PDF as raw bytes (ready for st.download_button or file write).
    """
    styles = _styles()
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18*mm, bottomMargin=16*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="EduGuard AI Evaluation Report",
    )

    doc_profile   = report_data.get("doc_profile", {}) or {}
    ai_detection  = report_data.get("ai_detection", {}) or {}
    viva_results  = report_data.get("viva_results", {}) or {}
    feedback      = report_data.get("feedback", {}) or {}
    roadmap       = report_data.get("study_roadmap", {}) or {}

    student_fb = feedback.get("student_feedback", {}) or {}
    prof_report = feedback.get("professor_report", {}) or {}

    story = []

    # ── Header ──
    story.append(Paragraph("EduGuard AI", styles["Title"]))
    story.append(Paragraph("Agentic Academic Integrity Framework — Evaluation Report", styles["Subtitle"]))
    meta_bits = [datetime.now().strftime("%d %B %Y, %I:%M %p")]
    if student_name:
        meta_bits.append(f"Student: {student_name}")
    if file_name:
        meta_bits.append(f"File: {file_name}")
    story.append(Paragraph("  •  ".join(meta_bits), styles["Meta"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ROSE_LIGHT, spaceAfter=10))

    # ── 1. Submission Overview ──
    story.append(Paragraph("Submission Overview", styles["SectionHeading"]))
    rows = [
        ("Topic", doc_profile.get("topic", "N/A")),
        ("Subject Area", doc_profile.get("subject_area", "N/A")),
        ("Academic Level", doc_profile.get("academic_level", "N/A")),
        ("Key Concepts", ", ".join(doc_profile.get("key_concepts", [])) or "N/A"),
    ]
    story.append(_metric_table(rows, styles))
    story.append(Spacer(1, 6))
    summary = doc_profile.get("summary", "")
    if summary:
        story.append(Paragraph(f"<b>Summary:</b> {summary}", styles["Body"]))

    # ── 2. AI Detection ──
    story.append(Paragraph("AI Involvement Analysis", styles["SectionHeading"]))
    story.append(_ai_table(ai_detection, styles))
    assessment = ai_detection.get("semantic_analysis", {}).get("overall_assessment", "")
    if assessment:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Assessment:</b> {assessment}", styles["Body"]))

    # ── 3. Viva Results ──
    story.append(Paragraph("Knowledge Verification — Viva Results", styles["SectionHeading"]))
    story.append(_score_table(viva_results, styles))
    story.append(Spacer(1, 10))

    qa_list = viva_results.get("questions_and_answers", [])
    if qa_list:
        story.append(Paragraph("Question-by-Question Breakdown", styles["SubHeading"]))
        for qa in qa_list:
            ev = qa.get("evaluation", {})
            qtype = qa.get("type", "mcq")
            level = qa.get("level", "")
            qno = qa.get("question_no", "")

            block = []
            block.append(Paragraph(
                f"Q{qno} &nbsp;·&nbsp; {level} &nbsp;·&nbsp; {'MCQ' if qtype=='mcq' else 'Short Answer'}",
                styles["QuestionLabel"]
            ))
            block.append(Paragraph(qa.get("question", ""), styles["QuestionText"]))

            if qtype == "mcq":
                is_correct = ev.get("is_correct", False)
                chip = _status_chip("Correct" if is_correct else "Incorrect",
                                    "green" if is_correct else "red")
                block.append(Paragraph(
                    f"Selected: <b>{ev.get('selected_option','-')}</b> &nbsp;|&nbsp; "
                    f"Correct: <b>{ev.get('correct_option','-')}</b> &nbsp; {chip}",
                    styles["AnswerText"]
                ))
            else:
                score = ev.get("score", 0)
                max_m = ev.get("max_marks", 0)
                block.append(Paragraph(f"<b>Answer:</b> {qa.get('student_answer','')}", styles["AnswerText"]))
                block.append(Paragraph(f"<b>Score:</b> {score}/{max_m}", styles["AnswerText"]))

            fb_text = ev.get("feedback", "")
            if fb_text:
                block.append(Paragraph(f"&rarr; {fb_text}", styles["FeedbackText"]))

            story.append(KeepTogether(block))
            story.append(Spacer(1, 4))

    # ── 4. Student Feedback ──
    story.append(Paragraph("Personalized Feedback for Student", styles["SectionHeading"]))
    if student_fb.get("overall_message"):
        story.append(Paragraph(student_fb["overall_message"], styles["Body"]))

    if student_fb.get("strengths"):
        story.append(Paragraph("Strengths", styles["SubHeading"]))
        for s in student_fb["strengths"]:
            story.append(Paragraph(f"• {s}", styles["Bullet"]))

    if student_fb.get("areas_to_improve"):
        story.append(Paragraph("Areas to Improve", styles["SubHeading"]))
        for a in student_fb["areas_to_improve"]:
            story.append(Paragraph(f"• {a}", styles["Bullet"]))

    if student_fb.get("immediate_action"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Immediate Action:</b> {student_fb['immediate_action']}", styles["Body"]))
    if student_fb.get("encouragement"):
        story.append(Paragraph(f"<i>{student_fb['encouragement']}</i>", styles["FeedbackText"]))

    # ── 5. Professor Report ──
    story.append(Paragraph("Professor Evaluation Report", styles["SectionHeading"]))
    concern = prof_report.get("integrity_concern_level", "N/A")
    rec = prof_report.get("recommended_action", "N/A")
    rows = [
        ("Integrity Concern", f'{concern} {_status_chip(concern, _risk_kind(concern) if concern in ("Low","Medium","High") else "blue")}'),
        ("Recommended Action", rec),
        ("AI Usage Assessment", prof_report.get("ai_usage_assessment", "N/A")),
        ("Understanding Assessment", prof_report.get("understanding_assessment", "N/A")),
    ]
    story.append(_metric_table(rows, styles))
    if prof_report.get("summary"):
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Summary:</b> {prof_report['summary']}", styles["Body"]))
    if prof_report.get("notes_for_professor"):
        story.append(Paragraph(f"<b>Notes:</b> {prof_report['notes_for_professor']}", styles["Body"]))

    # ── 6. Study Roadmap ──
    if roadmap.get("daily_plan"):
        story.append(Paragraph("Personalized Study Roadmap", styles["SectionHeading"]))
        story.append(Paragraph(roadmap.get("roadmap_title", "Study Plan"), styles["SubHeading"]))

        for day in roadmap.get("daily_plan", []):
            resources = " · ".join([f"{r.get('title','')} ({r.get('platform','')})" for r in day.get("resources", [])])
            day_block = [
                Paragraph(f"Day {day.get('day','')} — {day.get('focus_topic','')}", styles["DayTitle"]),
                Paragraph(f"<b>Goal:</b> {day.get('goal','')}", styles["DayBody"]),
            ]
            if day.get("tasks"):
                day_block.append(Paragraph(f"<b>Tasks:</b> {' | '.join(day['tasks'])}", styles["DayBody"]))
            if resources:
                day_block.append(Paragraph(f"<b>Resources:</b> {resources}", styles["DayBody"]))
            if day.get("practice"):
                day_block.append(Paragraph(f"<b>Practice:</b> {day['practice']}", styles["DayBody"]))
            day_block.append(Spacer(1, 6))
            story.append(KeepTogether(day_block))

        if roadmap.get("final_milestone"):
            story.append(Paragraph(f"<b>Final Milestone:</b> {roadmap['final_milestone']}", styles["Body"]))
        if roadmap.get("motivational_note"):
            story.append(Paragraph(f"<i>{roadmap['motivational_note']}</i>", styles["FeedbackText"]))

    # ── Footer ──
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.75, color=ROSE_LIGHT, spaceAfter=6))
    story.append(Paragraph(
        "Generated by EduGuard AI — Agentic Academic Integrity Framework. "
        "This report evaluates understanding alongside AI assistance, not as a replacement for human judgment.",
        styles["Footer"]
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
