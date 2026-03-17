"""Rich terminal reports for practice results and analysis."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scoremap.models import (
    AnswerRecord,
    SessionResult,
    StudyPlan,
    TopicPerformance,
)

console = Console()


def print_session_result(result: SessionResult) -> None:
    """Print a formatted practice session result."""
    accuracy_pct = result.accuracy * 100

    if accuracy_pct >= 80:
        color = "green"
        verdict = "Excellent"
    elif accuracy_pct >= 60:
        color = "yellow"
        verdict = "Good"
    else:
        color = "red"
        verdict = "Needs Work"

    header = Text(f"Session Complete - {verdict}", style=f"bold {color}")
    console.print()
    console.print(Panel(header, border_style=color))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Exam", result.exam_type.value.upper())
    table.add_row("Section", result.section)
    table.add_row("Questions", str(result.total_questions))
    table.add_row("Correct", f"{result.correct_count}/{result.total_questions}")
    table.add_row("Accuracy", f"[{color}]{accuracy_pct:.1f}%[/{color}]")
    table.add_row("Avg Time", f"{result.average_time_seconds:.1f}s per question")

    duration = (result.end_time - result.start_time).total_seconds()
    table.add_row("Duration", f"{duration:.0f}s total")

    console.print(table)
    console.print()


def print_question(question_num: int, total: int, question, difficulty: str) -> None:
    """Print a formatted question."""
    diff_colors = {"easy": "green", "medium": "yellow", "hard": "red"}
    color = diff_colors.get(difficulty, "white")

    console.print()
    console.print(
        f"[bold]Question {question_num}/{total}[/bold]  "
        f"[{color}][{difficulty.upper()}][/{color}]  "
        f"Topic: {question.topic.replace('_', ' ').title()}"
    )
    console.print()
    console.print(f"  {question.text}")
    console.print()

    if question.choices:
        for i, choice in enumerate(question.choices):
            label = chr(65 + i)  # A, B, C, D
            console.print(f"    [{label}] {choice}")
        console.print()


def print_answer_feedback(record: AnswerRecord, explanation: str = "") -> None:
    """Print feedback after answering a question."""
    if record.is_correct:
        console.print(f"  [bold green]Correct![/bold green]  ({record.time_spent_seconds:.1f}s)")
    else:
        console.print(
            f"  [bold red]Incorrect.[/bold red]  "
            f"Your answer: {record.user_answer}  "
            f"Correct: {record.correct_answer}  "
            f"({record.time_spent_seconds:.1f}s)"
        )
    if explanation:
        console.print(f"  [dim]{explanation}[/dim]")


def print_analysis_summary(summary: dict) -> None:
    """Print a comprehensive performance analysis."""
    console.print()
    console.print(
        Panel(
            f"[bold]Performance Analysis - {summary['exam_type'].upper()}[/bold]",
            border_style="blue",
        )
    )

    # Overview
    overview = Table(show_header=False, box=None, padding=(0, 2))
    overview.add_column("Metric", style="bold")
    overview.add_column("Value")

    overview.add_row("Total Questions", str(summary["total_questions"]))
    acc = summary["overall_accuracy"] * 100
    acc_color = "green" if acc >= 70 else "yellow" if acc >= 50 else "red"
    overview.add_row("Overall Accuracy", f"[{acc_color}]{acc:.1f}%[/{acc_color}]")

    if summary["estimated_score"] is not None:
        overview.add_row("Estimated Score", str(summary["estimated_score"]))

    trend = summary["score_trend"]
    trend_style = {
        "improving": "[green]Improving[/green]",
        "declining": "[red]Declining[/red]",
        "stable": "[yellow]Stable[/yellow]",
    }
    overview.add_row("Trend", trend_style.get(trend, trend))
    overview.add_row("Sessions", str(summary["sessions_completed"]))

    console.print(overview)
    console.print()

    # Section breakdown
    if summary["by_section"]:
        sec_table = Table(title="By Section", border_style="blue")
        sec_table.add_column("Section", style="bold")
        sec_table.add_column("Attempted", justify="right")
        sec_table.add_column("Correct", justify="right")
        sec_table.add_column("Accuracy", justify="right")
        sec_table.add_column("Avg Time", justify="right")

        for section, data in summary["by_section"].items():
            sec_acc = data["accuracy"] * 100
            color = "green" if sec_acc >= 70 else "yellow" if sec_acc >= 50 else "red"
            sec_table.add_row(
                section,
                str(data["total"]),
                str(data["correct"]),
                f"[{color}]{sec_acc:.1f}%[/{color}]",
                f"{data['average_time']:.1f}s",
            )
        console.print(sec_table)
        console.print()

    # Difficulty breakdown
    if summary["by_difficulty"]:
        diff_table = Table(title="By Difficulty", border_style="blue")
        diff_table.add_column("Difficulty", style="bold")
        diff_table.add_column("Attempted", justify="right")
        diff_table.add_column("Correct", justify="right")
        diff_table.add_column("Accuracy", justify="right")

        for diff in ["easy", "medium", "hard"]:
            if diff in summary["by_difficulty"]:
                data = summary["by_difficulty"][diff]
                d_acc = data["accuracy"] * 100
                color = "green" if d_acc >= 70 else "yellow" if d_acc >= 50 else "red"
                diff_table.add_row(
                    diff.title(),
                    str(data["total"]),
                    str(data["correct"]),
                    f"[{color}]{d_acc:.1f}%[/{color}]",
                )
        console.print(diff_table)
        console.print()

    # Weak areas
    if summary["weak_areas"]:
        console.print("[bold red]Weak Areas (Focus Here):[/bold red]")
        for area in summary["weak_areas"]:
            topic = area["topic"].replace("_", " ").title()
            console.print(f"  - {topic}: {area['accuracy']*100:.1f}%")
        console.print()

    # Strong areas
    if summary["strong_areas"]:
        console.print("[bold green]Strong Areas:[/bold green]")
        for area in summary["strong_areas"]:
            topic = area["topic"].replace("_", " ").title()
            console.print(f"  - {topic}: {area['accuracy']*100:.1f}%")
        console.print()


def print_study_plan(plan: StudyPlan) -> None:
    """Print a formatted study plan."""
    console.print()
    console.print(
        Panel(
            f"[bold]Study Plan - {plan.exam_type.value.upper()} "
            f"({plan.total_weeks} weeks, {plan.weekly_hours}h/week)[/bold]",
            border_style="green",
        )
    )

    if plan.priority_topics:
        console.print("[bold]Priority Topics:[/bold]")
        for topic in plan.priority_topics:
            console.print(f"  - {topic.replace('_', ' ').title()}")
        console.print()

    # Group blocks by week
    blocks_by_week: dict[int, list] = {}
    for block in plan.blocks:
        week = (block.day - 1) // 5 + 1
        blocks_by_week.setdefault(week, []).append(block)

    for week_num in sorted(blocks_by_week.keys()):
        week_blocks = blocks_by_week[week_num]

        table = Table(
            title=f"Week {week_num}",
            border_style="green",
            show_lines=True,
        )
        table.add_column("Day", justify="center", width=5)
        table.add_column("Topic", width=20)
        table.add_column("Focus", width=35)
        table.add_column("Time", justify="right", width=8)
        table.add_column("Questions", justify="right", width=10)

        diff_colors = {"easy": "green", "medium": "yellow", "hard": "red"}

        for block in week_blocks:
            day_in_week = ((block.day - 1) % 5) + 1
            topic_display = block.topic.replace("_", " ").title()
            color = diff_colors.get(block.difficulty.value, "white")
            table.add_row(
                str(day_in_week),
                topic_display,
                f"[{color}]{block.focus}[/{color}]",
                f"{block.duration_minutes}m",
                str(block.question_count),
            )

        console.print(table)
        console.print()
