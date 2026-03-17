"""Tests for the adaptive difficulty engine."""

from scoremap.models import AnswerRecord, Difficulty, ExamType
from scoremap.practice.adaptive import AdaptiveEngine, PerformanceWindow
from scoremap.practice.question_bank import QuestionBank


def _make_answer(
    question_id: str = "q1",
    topic: str = "algebra",
    difficulty: Difficulty = Difficulty.MEDIUM,
    is_correct: bool = True,
    time_spent: float = 60.0,
) -> AnswerRecord:
    """Helper to create an answer record."""
    return AnswerRecord(
        question_id=question_id,
        exam_type=ExamType.SAT,
        section="math",
        topic=topic,
        difficulty=difficulty,
        user_answer="5" if is_correct else "wrong",
        correct_answer="5",
        is_correct=is_correct,
        time_spent_seconds=time_spent,
    )


class TestPerformanceWindow:
    def test_empty_window_accuracy(self):
        window = PerformanceWindow()
        assert window.accuracy == 0.5  # Default when no data

    def test_all_correct(self):
        window = PerformanceWindow(window_size=5)
        for _ in range(5):
            window.add(True)
        assert window.accuracy == 1.0

    def test_all_incorrect(self):
        window = PerformanceWindow(window_size=5)
        for _ in range(5):
            window.add(False)
        assert window.accuracy == 0.0

    def test_sliding_window(self):
        window = PerformanceWindow(window_size=3)
        window.add(False)
        window.add(False)
        window.add(False)
        window.add(True)
        window.add(True)
        window.add(True)
        # Last 3 are all True
        assert window.accuracy == 1.0

    def test_mixed_performance(self):
        window = PerformanceWindow(window_size=4)
        window.add(True)
        window.add(False)
        window.add(True)
        window.add(False)
        assert window.accuracy == 0.5


class TestAdaptiveEngine:
    def _make_engine(
        self, difficulty: Difficulty = Difficulty.MEDIUM
    ) -> AdaptiveEngine:
        bank = QuestionBank(ExamType.SAT)
        return AdaptiveEngine(
            bank, initial_difficulty=difficulty, window_size=3
        )

    def test_initial_difficulty(self):
        engine = self._make_engine(Difficulty.EASY)
        assert engine.current_difficulty == Difficulty.EASY

    def test_promotes_on_high_accuracy(self):
        engine = self._make_engine(Difficulty.EASY)
        # Answer 3 correct in a row (window=3, accuracy=100% > 75%)
        for i in range(3):
            record = _make_answer(question_id=f"sat-math-00{i+1}", is_correct=True)
            engine.record_answer(record)

        # Trigger difficulty adjustment via next_question
        engine._adjust_difficulty()
        assert engine.current_difficulty == Difficulty.MEDIUM

    def test_demotes_on_low_accuracy(self):
        engine = self._make_engine(Difficulty.MEDIUM)
        # Answer 3 wrong in a row (accuracy=0% < 40%)
        for i in range(3):
            record = _make_answer(
                question_id=f"sat-math-00{i+1}",
                is_correct=False,
                difficulty=Difficulty.MEDIUM,
            )
            engine.record_answer(record)

        engine._adjust_difficulty()
        assert engine.current_difficulty == Difficulty.EASY

    def test_stays_at_same_level(self):
        engine = self._make_engine(Difficulty.MEDIUM)
        # 2 correct, 1 wrong = 66% (between 40% and 75%)
        engine.record_answer(_make_answer(question_id="sat-math-001", is_correct=True))
        engine.record_answer(_make_answer(question_id="sat-math-002", is_correct=True))
        engine.record_answer(_make_answer(question_id="sat-math-003", is_correct=False))

        engine._adjust_difficulty()
        assert engine.current_difficulty == Difficulty.MEDIUM

    def test_cannot_promote_past_hard(self):
        engine = self._make_engine(Difficulty.HARD)
        for i in range(3):
            engine.record_answer(
                _make_answer(question_id=f"sat-math-00{i+1}", is_correct=True)
            )
        engine._adjust_difficulty()
        assert engine.current_difficulty == Difficulty.HARD

    def test_cannot_demote_past_easy(self):
        engine = self._make_engine(Difficulty.EASY)
        for i in range(3):
            engine.record_answer(
                _make_answer(question_id=f"sat-math-00{i+1}", is_correct=False)
            )
        engine._adjust_difficulty()
        assert engine.current_difficulty == Difficulty.EASY

    def test_tracks_topic_accuracy(self):
        engine = self._make_engine()
        engine.record_answer(
            _make_answer(question_id="sat-math-001", topic="algebra", is_correct=True)
        )
        engine.record_answer(
            _make_answer(question_id="sat-math-002", topic="algebra", is_correct=False)
        )
        assert engine.get_topic_accuracy("algebra") == 0.5

    def test_next_question_returns_question(self):
        engine = self._make_engine(Difficulty.EASY)
        question = engine.next_question(section="math")
        assert question is not None
        assert question.exam_type == ExamType.SAT

    def test_next_question_prefers_weak_topics(self):
        engine = self._make_engine(Difficulty.EASY)
        # Make 'algebra' strong
        for i in range(3):
            engine.record_answer(
                _make_answer(
                    question_id=f"sat-math-00{i+1}",
                    topic="algebra",
                    is_correct=True,
                )
            )
        # The next question should prefer a weaker topic
        question = engine.next_question(section="math")
        if question is not None:
            # It should pick a topic other than algebra if available
            # (since algebra accuracy is high)
            assert question.topic != "algebra" or engine.bank.available_count <= 3

    def test_state_summary(self):
        engine = self._make_engine()
        engine.record_answer(_make_answer(question_id="sat-math-001", is_correct=True))
        summary = engine.get_state_summary()
        assert "current_difficulty" in summary
        assert "overall_accuracy" in summary
        assert summary["questions_answered"] == 1
