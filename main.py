import os
import sys
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

load_dotenv()
console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]EduGuard AI[/bold cyan]\n"
        "[white]Agentic Academic Integrity Framework[/white]\n"
        "[dim]Evaluating Understanding, Not Just Output[/dim]",
        border_style="cyan",
        padding=(1, 4),
    ))


def print_final_report(final_state: dict):
    """Print a beautiful final summary report."""
    console.print("\n")
    console.print(Panel("[bold white]FINAL EVALUATION REPORT[/bold white]",
                        border_style="bright_blue", expand=True))

    doc_profile  = final_state.get("doc_profile", {})
    ai_detection = final_state.get("ai_detection", {})
    viva_results = final_state.get("viva_results", {})
    feedback     = final_state.get("feedback", {})
    roadmap      = final_state.get("study_roadmap", {})

    # ── Document Info ──
    console.print("\n[bold cyan]📄 Submission[/bold cyan]")
    console.print(f"  Topic        : {doc_profile.get('topic', 'N/A')}")
    console.print(f"  Subject Area : {doc_profile.get('subject_area', 'N/A')}")
    console.print(f"  Level        : {doc_profile.get('academic_level', 'N/A')}")
    console.print(f"  Summary      : {doc_profile.get('summary', 'N/A')}")

    # ── Scores Table ──
    console.print("\n[bold cyan]📊 Evaluation Scores[/bold cyan]")
    table = Table(box=box.ROUNDED, border_style="blue", show_header=True, header_style="bold white")
    table.add_column("Metric",          style="white",       width=28)
    table.add_column("Score / Value",   style="bold yellow", width=20)
    table.add_column("Status",          style="green",       width=20)

    ai_score      = ai_detection.get("ai_involvement_score", 0)
    ai_label      = ai_detection.get("label", "N/A")
    risk          = ai_detection.get("risk_level", "N/A")
    viva_pct      = viva_results.get("percentage", 0)
    understanding = viva_results.get("understanding_level", "N/A")
    prof_report   = feedback.get("professor_report", {})
    recommendation = prof_report.get("recommended_action", "N/A")

    risk_color = {"Low": "green", "Medium": "yellow", "High": "red"}.get(risk, "white")
    und_color  = {"Excellent": "green", "Good": "cyan", "Moderate": "yellow", "Poor": "red"}.get(understanding, "white")

    table.add_row("AI Involvement",       f"{ai_score}%",            f"[{risk_color}]{ai_label}[/{risk_color}]")
    table.add_row("Risk Level",           risk,                      f"[{risk_color}]{risk}[/{risk_color}]")
    table.add_row("Viva Score",           f"{viva_pct}%",            f"[{und_color}]{understanding}[/{und_color}]")
    table.add_row("Integrity Concern",    prof_report.get("integrity_concern_level", "N/A"), "")
    table.add_row("Recommendation",       recommendation,            "")
    console.print(table)

    # ── Student Feedback ──
    student_fb = feedback.get("student_feedback", {})
    console.print("\n[bold cyan]💬 Student Feedback[/bold cyan]")
    console.print(f"  {student_fb.get('overall_message', '')}")
    console.print(f"\n  [green]Strengths[/green]      : {', '.join(student_fb.get('strengths', []))}")
    console.print(f"  [yellow]Improve[/yellow]        : {', '.join(student_fb.get('areas_to_improve', []))}")
    console.print(f"  [cyan]Action Now[/cyan]     : {student_fb.get('immediate_action', '')}")
    console.print(f"  [magenta]Motivation[/magenta]     : {student_fb.get('encouragement', '')}")

    # ── Weak Concepts ──
    weak = viva_results.get("weak_concepts", [])
    if weak:
        console.print(f"\n  [red]Weak Concepts[/red]  : {', '.join(weak)}")

    # ── Roadmap Summary ──
    console.print("\n[bold cyan]🗓️  Study Roadmap[/bold cyan]")
    console.print(f"  Plan           : {roadmap.get('roadmap_title', 'N/A')}")
    console.print(f"  Final Goal     : {roadmap.get('final_milestone', 'N/A')}")
    for day in roadmap.get("daily_plan", []):
        console.print(f"  Day {day['day']:>2}         : {day.get('focus_topic')} — {day.get('goal')}")

    # ── Professor Report ──
    console.print("\n[bold cyan]👨‍🏫 Professor Report[/bold cyan]")
    console.print(f"  {prof_report.get('summary', '')}")
    console.print(f"  Notes          : {prof_report.get('notes_for_professor', '')}")

    console.print("\n" + "─" * 60)
    console.print("[bold green]  EduGuard AI evaluation complete.[/bold green]")
    console.print("─" * 60 + "\n")


def save_report(final_state: dict, output_path: str = "eduguard_report.json"):
    """Save the full report to a JSON file."""
    # Remove raw_text from saved report (too large)
    report = {k: v for k, v in final_state.items() if k not in ("raw_text", "groq_api_key")}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    console.print(f"  [dim]Full report saved to: {output_path}[/dim]")


def main():
    print_banner()

    # ── Get API Key ──
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        console.print("[red]Error: GROQ_API_KEY not found in environment.[/red]")
        console.print("  Set it in a .env file: GROQ_API_KEY=your_key_here")
        sys.exit(1)

    # ── Get File Path ──
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        console.print("\n[white]Supported formats: PDF, DOCX, PPTX, PY, JS, TXT[/white]")
        file_path = input("\nEnter path to student submission file: ").strip()

    if not os.path.exists(file_path):
        console.print(f"[red]File not found: {file_path}[/red]")
        sys.exit(1)

    console.print(f"\n[dim]Processing: {file_path}[/dim]\n")

    # ── Run Pipeline ──
    from graph.workflow import run_eduguard_pipeline

    try:
        final_state = run_eduguard_pipeline(file_path, groq_api_key)
    except Exception as e:
        console.print(f"[red]Pipeline error: {e}[/red]")
        raise

    if final_state.get("error"):
        console.print(f"[red]Error: {final_state['error']}[/red]")
        sys.exit(1)

    # ── Print + Save Report ──
    print_final_report(final_state)
    save_report(final_state)


if __name__ == "__main__":
    main()
