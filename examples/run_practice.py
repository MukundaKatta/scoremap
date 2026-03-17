"""Example: Run a simulated practice session programmatically."""

from scoremap.analyzer import PerformanceAnalyzer
from scoremap.models import Difficulty, ExamType, UserProfile
from scoremap.planner import StudyPlanner
from scoremap.practice.session import PracticeSession
from scoremap.report import (
    print_analysis_summary,
    print_session_result,
    print_study_plan,
)


def run_simulated_session() -> None:
    """Run a practice session with automatic answers for demonstration."""
    print("=" * 60)
    print("SCOREMAP - Simulated Practice Session")
    print("=" * 60)

    # Create a practice session
    session = PracticeSession(
        exam_type=ExamType.SAT,
        section="math",
        question_count=8,
        initial_difficulty=Difficulty.EASY,
    )

    question = session.start()
    q_num = 0

    while question is not None:
        q_num += 1
        print(f"\nQ{q_num}: [{question.difficulty.value.upper()}] {question.text}")

        # Simulate: always answer with the correct answer for demo
        record = session.submit_answer(question.correct_answer)
        status = "CORRECT" if record.is_correct else "WRONG"
        print(f"  -> {status} (difficulty now: {session.engine.current_difficulty.value})")

        question = session.next_question()

    result = session.finish()
    print_session_result(result)

    # Build a profile from the session
    profile = UserProfile(exam_type=ExamType.SAT)
    profile.all_answers = result.answers
    profile.sessions.append(result)

    # Analyze
    analyzer = PerformanceAnalyzer(profile)
    summary = analyzer.get_summary()
    print_analysis_summary(summary)

    # Generate study plan
    planner = StudyPlanner(profile, weekly_hours=8)
    plan = planner.generate_plan(weeks=2)
    print_study_plan(plan)


if __name__ == "__main__":
    run_simulated_session()
