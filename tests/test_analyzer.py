"""Tests for the performance analyzer."""

from datetime import datetime, timedelta

from scoremap.analyzer import PerformanceAnalyzer
from scoremap.models import (
    AnswerRecord,
    Difficulty,
    ExamType,
    SessionResult,
    UserProfile,
)


def _make_profile_with_answers(
    answers: list[AnswerRecord],
) -> UserProfile:
    """Create a profile with the given answers."""
    profile = UserProfile(exam_type=ExamType.SAT)
    profile.all_answers = answers
    return profile


def _make_answer(
    topic: str = "algebra",
    section: str = "math",
    difficulty: Difficulty = Difficulty.MEDIUM,
    is_correct: bool = True,
    time_spent: float = 60.0,
) -> AnswerRecord:
    return AnswerRecord(
        question_id=f"q-{topic}-{difficulty.value}",
        exam_type=ExamType.SAT,
        section=section,
        topic=topic,
        difficulty=difficulty,
        user_answer="correct" if is_correct else "wrong",
        correct_answer="correct",
        is_correct=is_correct,
        time_spent_seconds=time_spent,
    )


class TestPerformanceAnalyzer:
    def test_empty_profile(self):
        profile = UserProfile(exam_type=ExamType.SAT)
        analyzer = PerformanceAnalyzer(profile)
        assert analyzer.total_questions_attempted == 0
        assert analyzer.overall_accuracy == 0.0

    def test_overall_accuracy(self):
        answers = [
            _make_answer(is_correct=True),
            _make_answer(is_correct=True),
            _make_answer(is_correct=False),
            _make_answer(is_correct=True),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)
        assert analyzer.overall_accuracy == 0.75

    def test_analyze_by_topic(self):
        answers = [
            _make_answer(topic="algebra", is_correct=True),
            _make_answer(topic="algebra", is_correct=False),
            _make_answer(topic="geometry_trig", is_correct=True),
            _make_answer(topic="geometry_trig", is_correct=True),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        topics = analyzer.analyze_by_topic()
        topic_map = {tp.topic: tp for tp in topics}

        assert topic_map["algebra"].accuracy == 0.5
        assert topic_map["geometry_trig"].accuracy == 1.0

    def test_analyze_by_section(self):
        answers = [
            _make_answer(section="math", is_correct=True),
            _make_answer(section="math", is_correct=False),
            _make_answer(section="reading_writing", topic="vocabulary", is_correct=True),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        sections = analyzer.analyze_by_section()
        assert sections["math"]["accuracy"] == 0.5
        assert sections["reading_writing"]["accuracy"] == 1.0

    def test_analyze_by_difficulty(self):
        answers = [
            _make_answer(difficulty=Difficulty.EASY, is_correct=True),
            _make_answer(difficulty=Difficulty.EASY, is_correct=True),
            _make_answer(difficulty=Difficulty.HARD, is_correct=False),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        by_diff = analyzer.analyze_by_difficulty()
        assert by_diff["easy"]["accuracy"] == 1.0
        assert by_diff["hard"]["accuracy"] == 0.0

    def test_identify_weak_areas(self):
        answers = [
            _make_answer(topic="algebra", is_correct=True),
            _make_answer(topic="algebra", is_correct=True),
            _make_answer(topic="geometry_trig", is_correct=False),
            _make_answer(topic="geometry_trig", is_correct=False),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        weak = analyzer.identify_weak_areas(threshold=0.60)
        assert len(weak) == 1
        assert weak[0].topic == "geometry_trig"

    def test_identify_strong_areas(self):
        answers = [
            _make_answer(topic="algebra", is_correct=True),
            _make_answer(topic="algebra", is_correct=True),
            _make_answer(topic="geometry_trig", is_correct=False),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        strong = analyzer.identify_strong_areas(threshold=0.80)
        assert len(strong) == 1
        assert strong[0].topic == "algebra"

    def test_estimated_score(self):
        answers = [
            _make_answer(is_correct=True),
            _make_answer(is_correct=True),
            _make_answer(is_correct=False),
            _make_answer(is_correct=True),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        score = analyzer.get_estimated_score()
        assert score is not None
        # SAT range: 400-1600, 75% accuracy -> 400 + 0.75*1200 = 1300
        assert score == 1300

    def test_score_trend_insufficient_data(self):
        profile = UserProfile(exam_type=ExamType.SAT)
        analyzer = PerformanceAnalyzer(profile)
        assert analyzer.get_score_trend() == "insufficient_data"

    def test_score_trend_with_sessions(self):
        profile = UserProfile(exam_type=ExamType.SAT)
        now = datetime.now()

        # Create two sessions: first worse, second better
        session1 = SessionResult(
            exam_type=ExamType.SAT,
            section="math",
            answers=[],
            start_time=now - timedelta(days=10),
            end_time=now - timedelta(days=10),
            total_questions=10,
            correct_count=4,
            accuracy=0.4,
            average_time_seconds=60.0,
        )
        session2 = SessionResult(
            exam_type=ExamType.SAT,
            section="math",
            answers=[],
            start_time=now - timedelta(days=1),
            end_time=now - timedelta(days=1),
            total_questions=10,
            correct_count=8,
            accuracy=0.8,
            average_time_seconds=55.0,
        )
        profile.sessions = [session1, session2]

        analyzer = PerformanceAnalyzer(profile)
        trend = analyzer.get_score_trend()
        assert trend == "improving"

    def test_get_summary(self):
        answers = [
            _make_answer(is_correct=True),
            _make_answer(is_correct=False),
        ]
        profile = _make_profile_with_answers(answers)
        analyzer = PerformanceAnalyzer(profile)

        summary = analyzer.get_summary()
        assert summary["exam_type"] == "sat"
        assert summary["total_questions"] == 2
        assert "weak_areas" in summary
        assert "strong_areas" in summary
        assert "by_section" in summary
        assert "by_difficulty" in summary
