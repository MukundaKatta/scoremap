"""Timed practice sessions with score tracking."""

from __future__ import annotations

import time
from datetime import datetime

from scoremap.models import (
    AnswerRecord,
    Difficulty,
    ExamType,
    Question,
    SessionResult,
)
from scoremap.practice.adaptive import AdaptiveEngine
from scoremap.practice.question_bank import QuestionBank


class PracticeSession:
    """Manages a timed practice session with adaptive difficulty.

    Provides questions one at a time, tracks timing and scores,
    and produces a SessionResult when complete.
    """

    def __init__(
        self,
        exam_type: ExamType,
        section: str | None = None,
        question_count: int = 10,
        initial_difficulty: Difficulty = Difficulty.MEDIUM,
        time_limit_minutes: int | None = None,
    ) -> None:
        self.exam_type = exam_type
        self.section = section
        self.question_count = question_count
        self.time_limit_minutes = time_limit_minutes

        self.bank = QuestionBank(exam_type)
        self.engine = AdaptiveEngine(
            self.bank,
            initial_difficulty=initial_difficulty,
        )

        self.answers: list[AnswerRecord] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self._current_question: Question | None = None
        self._question_start: float = 0.0
        self._questions_served = 0

    @property
    def is_complete(self) -> bool:
        """Check if session is done."""
        if self._questions_served >= self.question_count:
            return True
        if self.time_limit_minutes and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed >= self.time_limit_minutes * 60:
                return True
        return False

    @property
    def correct_count(self) -> int:
        return sum(1 for a in self.answers if a.is_correct)

    @property
    def accuracy(self) -> float:
        if not self.answers:
            return 0.0
        return self.correct_count / len(self.answers)

    def start(self) -> Question | None:
        """Begin the session and return the first question."""
        self.start_time = datetime.now()
        return self.next_question()

    def next_question(self) -> Question | None:
        """Get the next adaptive question."""
        if self.is_complete:
            return None

        question = self.engine.next_question(section=self.section)
        if question is None:
            return None

        self._current_question = question
        self._question_start = time.time()
        self._questions_served += 1
        return question

    def submit_answer(self, user_answer: str) -> AnswerRecord:
        """Submit an answer for the current question and get feedback."""
        if self._current_question is None:
            raise ValueError("No current question. Call next_question() first.")

        question = self._current_question
        time_spent = time.time() - self._question_start

        is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()

        record = AnswerRecord(
            question_id=question.id,
            exam_type=self.exam_type,
            section=question.section,
            topic=question.topic,
            difficulty=question.difficulty,
            user_answer=user_answer,
            correct_answer=question.correct_answer,
            is_correct=is_correct,
            time_spent_seconds=round(time_spent, 1),
        )

        self.answers.append(record)
        self.engine.record_answer(record)
        self._current_question = None

        return record

    def finish(self) -> SessionResult:
        """End the session and produce a result summary."""
        self.end_time = datetime.now()
        if self.start_time is None:
            self.start_time = self.end_time

        total_time = sum(a.time_spent_seconds for a in self.answers)
        avg_time = total_time / len(self.answers) if self.answers else 0.0

        return SessionResult(
            exam_type=self.exam_type,
            section=self.section or "all",
            answers=self.answers,
            start_time=self.start_time,
            end_time=self.end_time,
            total_questions=len(self.answers),
            correct_count=self.correct_count,
            accuracy=round(self.accuracy, 3),
            average_time_seconds=round(avg_time, 1),
        )

    def get_progress(self) -> dict:
        """Return current session progress."""
        return {
            "questions_answered": len(self.answers),
            "questions_remaining": max(0, self.question_count - self._questions_served),
            "correct": self.correct_count,
            "accuracy": round(self.accuracy * 100, 1),
            "current_difficulty": self.engine.current_difficulty.value,
            "adaptive_state": self.engine.get_state_summary(),
        }
