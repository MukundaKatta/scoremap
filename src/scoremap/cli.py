"""CLI interface for SCOREMAP using Click."""

from __future__ import annotations

import click
from rich.console import Console

from scoremap.analyzer import PerformanceAnalyzer
from scoremap.exams import get_exam_definition, get_sections
from scoremap.models import Difficulty, ExamType, UserProfile
from scoremap.planner import StudyPlanner
from scoremap.practice.session import PracticeSession
from scoremap.report import (
    print_analysis_summary,
    print_answer_feedback,
    print_question,
    print_session_result,
    print_study_plan,
)

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="scoremap")
def cli() -> None:
    """SCOREMAP - AI Test Prep Coach.

    Adaptive practice, performance analysis, and personalized study planning
    for standardized exams (SAT, GRE, GMAT).
    """


@cli.command()
@click.option(
    "--exam",
    type=click.Choice(["sat", "gre", "gmat"], case_sensitive=False),
    required=True,
    help="Exam type to practice.",
)
@click.option("--section", type=str, default=None, help="Specific section to practice.")
@click.option("--count", type=int, default=10, help="Number of questions.")
@click.option(
    "--difficulty",
    type=click.Choice(["easy", "medium", "hard"], case_sensitive=False),
    default="medium",
    help="Starting difficulty level.",
)
@click.option("--time-limit", type=int, default=None, help="Time limit in minutes.")
def practice(
    exam: str,
    section: str | None,
    count: int,
    difficulty: str,
    time_limit: int | None,
) -> None:
    """Start an adaptive practice session."""
    exam_type = ExamType(exam.lower())
    initial_difficulty = Difficulty(difficulty.lower())

    # Validate section
    valid_sections = get_sections(exam_type)
    if section and section not in valid_sections:
        console.print(f"[red]Invalid section '{section}'. Valid: {', '.join(valid_sections)}[/red]")
        raise SystemExit(1)

    exam_def = get_exam_definition(exam_type)
    console.print(f"\n[bold blue]SCOREMAP Practice - {exam_def.name}[/bold blue]")
    if section:
        console.print(f"Section: {section}")
    console.print(f"Questions: {count} | Starting difficulty: {difficulty}")
    console.print("[dim]Type your answer (A/B/C/D or the answer text). Type 'q' to quit.[/dim]\n")

    session = PracticeSession(
        exam_type=exam_type,
        section=section,
        question_count=count,
        initial_difficulty=initial_difficulty,
        time_limit_minutes=time_limit,
    )

    question = session.start()
    q_num = 0

    while question is not None:
        q_num += 1
        print_question(q_num, count, question, question.difficulty.value)

        user_input = click.prompt("  Your answer", type=str).strip()

        if user_input.lower() == "q":
            console.print("\n[yellow]Session ended early.[/yellow]")
            break

        # Map letter answers to choice text
        answer = user_input
        if len(user_input) == 1 and user_input.upper() in "ABCD" and question.choices:
            idx = ord(user_input.upper()) - 65
            if 0 <= idx < len(question.choices):
                answer = question.choices[idx]

        record = session.submit_answer(answer)
        print_answer_feedback(record, question.explanation)

        # Show progress
        progress = session.get_progress()
        console.print(
            f"  [dim]Progress: {progress['correct']}/{q_num} correct | "
            f"Difficulty: {progress['current_difficulty']}[/dim]"
        )

        question = session.next_question()

    result = session.finish()
    print_session_result(result)


@cli.command()
@click.option(
    "--exam",
    type=click.Choice(["sat", "gre", "gmat"], case_sensitive=False),
    required=True,
    help="Exam type to analyze.",
)
def analyze(exam: str) -> None:
    """Analyze your practice performance.

    Note: In this demo, a simulated session is analyzed.
    In production, this would load history from a database.
    """
    exam_type = ExamType(exam.lower())

    # Create a demo profile with simulated data for demonstration
    profile = _create_demo_profile(exam_type)
    analyzer = PerformanceAnalyzer(profile)
    summary = analyzer.get_summary()
    print_analysis_summary(summary)


@cli.command()
@click.option(
    "--exam",
    type=click.Choice(["sat", "gre", "gmat"], case_sensitive=False),
    required=True,
    help="Exam type to plan for.",
)
@click.option("--weeks", type=int, default=4, help="Number of weeks for the plan.")
@click.option("--hours", type=float, default=10.0, help="Weekly study hours.")
def plan(exam: str, weeks: int, hours: float) -> None:
    """Generate a personalized study plan."""
    exam_type = ExamType(exam.lower())

    # Create a demo profile for plan generation
    profile = _create_demo_profile(exam_type)
    planner = StudyPlanner(profile, weekly_hours=hours)
    study_plan = planner.generate_plan(weeks=weeks)
    print_study_plan(study_plan)


def _create_demo_profile(exam_type: ExamType) -> UserProfile:
    """Create a demo profile with simulated practice data for demonstration."""
    import random
    from datetime import datetime, timedelta

    from scoremap.exams import get_questions
    from scoremap.models import AnswerRecord, SessionResult

    random.seed(42)
    profile = UserProfile(exam_type=exam_type)
    questions = get_questions(exam_type)

    all_answers: list[AnswerRecord] = []
    for q in questions:
        # Simulate varied performance: easier questions more likely correct
        if q.difficulty == Difficulty.EASY:
            correct_prob = 0.85
        elif q.difficulty == Difficulty.MEDIUM:
            correct_prob = 0.60
        else:
            correct_prob = 0.35

        is_correct = random.random() < correct_prob
        record = AnswerRecord(
            question_id=q.id,
            exam_type=exam_type,
            section=q.section,
            topic=q.topic,
            difficulty=q.difficulty,
            user_answer=q.correct_answer if is_correct else "wrong",
            correct_answer=q.correct_answer,
            is_correct=is_correct,
            time_spent_seconds=random.uniform(30, 150),
            timestamp=datetime.now() - timedelta(days=random.randint(1, 30)),
        )
        all_answers.append(record)

    profile.all_answers = all_answers

    # Create a simulated session
    if all_answers:
        correct_count = sum(1 for a in all_answers if a.is_correct)
        session = SessionResult(
            exam_type=exam_type,
            section="all",
            answers=all_answers,
            start_time=datetime.now() - timedelta(hours=1),
            end_time=datetime.now(),
            total_questions=len(all_answers),
            correct_count=correct_count,
            accuracy=correct_count / len(all_answers),
            average_time_seconds=sum(a.time_spent_seconds for a in all_answers)
            / len(all_answers),
        )
        profile.sessions.append(session)

    return profile


if __name__ == "__main__":
    cli()
