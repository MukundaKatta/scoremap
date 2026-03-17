"""Question bank with categorized practice questions."""

from __future__ import annotations

from scoremap.exams import get_questions
from scoremap.models import Difficulty, ExamType, Question


class QuestionBank:
    """Manages and filters practice questions by exam, section, topic, and difficulty."""

    def __init__(self, exam_type: ExamType) -> None:
        self.exam_type = exam_type
        self._questions = get_questions(exam_type)
        self._used_ids: set[str] = set()

    @property
    def total_count(self) -> int:
        return len(self._questions)

    @property
    def available_count(self) -> int:
        return len([q for q in self._questions if q.id not in self._used_ids])

    def get_sections(self) -> list[str]:
        """Return all unique sections."""
        return sorted({q.section for q in self._questions})

    def get_topics(self, section: str | None = None) -> list[str]:
        """Return all unique topics, optionally filtered by section."""
        questions = self._questions
        if section:
            questions = [q for q in questions if q.section == section]
        return sorted({q.topic for q in questions})

    def filter(
        self,
        section: str | None = None,
        topic: str | None = None,
        difficulty: Difficulty | None = None,
        exclude_used: bool = True,
    ) -> list[Question]:
        """Filter questions by criteria."""
        results = list(self._questions)

        if section:
            results = [q for q in results if q.section == section]
        if topic:
            results = [q for q in results if q.topic == topic]
        if difficulty:
            results = [q for q in results if q.difficulty == difficulty]
        if exclude_used:
            results = [q for q in results if q.id not in self._used_ids]

        return results

    def get_by_difficulty(
        self,
        difficulty: Difficulty,
        section: str | None = None,
        count: int = 5,
    ) -> list[Question]:
        """Get questions at a specific difficulty level."""
        pool = self.filter(section=section, difficulty=difficulty)
        return pool[:count]

    def mark_used(self, question_id: str) -> None:
        """Mark a question as used to avoid repetition."""
        self._used_ids.add(question_id)

    def reset(self) -> None:
        """Reset used tracking."""
        self._used_ids.clear()

    def get_difficulty_distribution(self, section: str | None = None) -> dict[str, int]:
        """Return count of questions per difficulty level."""
        questions = self.filter(section=section, exclude_used=False)
        dist: dict[str, int] = {d.value: 0 for d in Difficulty}
        for q in questions:
            dist[q.difficulty.value] += 1
        return dist
