"""Adaptive difficulty engine that adjusts questions based on performance."""

from __future__ import annotations

from dataclasses import dataclass, field

from scoremap.models import AnswerRecord, Difficulty, ExamType, Question
from scoremap.practice.question_bank import QuestionBank


@dataclass
class PerformanceWindow:
    """Sliding window of recent performance for adaptive decisions."""

    window_size: int = 5
    records: list[bool] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if not self.records:
            return 0.5
        recent = self.records[-self.window_size :]
        return sum(recent) / len(recent)

    def add(self, correct: bool) -> None:
        self.records.append(correct)


# Thresholds for difficulty transitions
PROMOTE_THRESHOLD = 0.75  # Move up if >= 75% accuracy
DEMOTE_THRESHOLD = 0.40   # Move down if < 40% accuracy

DIFFICULTY_ORDER = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]


class AdaptiveEngine:
    """Adjusts question difficulty based on rolling performance.

    Algorithm:
    - Maintains a sliding window of the last N answers (default 5).
    - If accuracy in the window >= 75%, promote to the next difficulty level.
    - If accuracy in the window < 40%, demote to the previous difficulty level.
    - Otherwise, stay at the current level.
    - Considers per-topic performance to avoid promoting in weak areas.
    """

    def __init__(
        self,
        question_bank: QuestionBank,
        initial_difficulty: Difficulty = Difficulty.MEDIUM,
        window_size: int = 5,
        promote_threshold: float = PROMOTE_THRESHOLD,
        demote_threshold: float = DEMOTE_THRESHOLD,
    ) -> None:
        self.bank = question_bank
        self.current_difficulty = initial_difficulty
        self.promote_threshold = promote_threshold
        self.demote_threshold = demote_threshold

        # Overall performance window
        self._overall_window = PerformanceWindow(window_size=window_size)

        # Per-topic performance windows
        self._topic_windows: dict[str, PerformanceWindow] = {}

        # History of difficulty changes
        self.difficulty_history: list[Difficulty] = [initial_difficulty]

    @property
    def overall_accuracy(self) -> float:
        return self._overall_window.accuracy

    def get_topic_accuracy(self, topic: str) -> float:
        if topic not in self._topic_windows:
            return 0.5
        return self._topic_windows[topic].accuracy

    def record_answer(self, answer: AnswerRecord) -> None:
        """Record an answer and update performance tracking."""
        self._overall_window.add(answer.is_correct)

        if answer.topic not in self._topic_windows:
            self._topic_windows[answer.topic] = PerformanceWindow()
        self._topic_windows[answer.topic].add(answer.is_correct)

        self.bank.mark_used(answer.question_id)

    def _adjust_difficulty(self) -> Difficulty:
        """Determine the next difficulty level based on performance."""
        accuracy = self._overall_window.accuracy
        current_idx = DIFFICULTY_ORDER.index(self.current_difficulty)

        if accuracy >= self.promote_threshold and current_idx < len(DIFFICULTY_ORDER) - 1:
            new_difficulty = DIFFICULTY_ORDER[current_idx + 1]
        elif accuracy < self.demote_threshold and current_idx > 0:
            new_difficulty = DIFFICULTY_ORDER[current_idx - 1]
        else:
            new_difficulty = self.current_difficulty

        if new_difficulty != self.current_difficulty:
            self.current_difficulty = new_difficulty
            self.difficulty_history.append(new_difficulty)

        return self.current_difficulty

    def next_question(self, section: str | None = None) -> Question | None:
        """Select the next question with adaptive difficulty.

        Strategy:
        1. Adjust difficulty based on recent performance.
        2. Try to pick a question at the target difficulty.
        3. If none available, try adjacent difficulties.
        4. Prefer topics where the user is weakest.
        """
        target_difficulty = self._adjust_difficulty()

        # Get available questions at the target difficulty
        candidates = self.bank.filter(
            section=section,
            difficulty=target_difficulty,
        )

        # Fall back to adjacent difficulties if needed
        if not candidates:
            idx = DIFFICULTY_ORDER.index(target_difficulty)
            for offset in [1, -1, 2, -2]:
                adj_idx = idx + offset
                if 0 <= adj_idx < len(DIFFICULTY_ORDER):
                    candidates = self.bank.filter(
                        section=section,
                        difficulty=DIFFICULTY_ORDER[adj_idx],
                    )
                    if candidates:
                        break

        if not candidates:
            return None

        # Sort by topic weakness: prioritize topics where user is struggling
        candidates.sort(key=lambda q: self.get_topic_accuracy(q.topic))

        return candidates[0]

    def get_state_summary(self) -> dict:
        """Return current state of the adaptive engine."""
        return {
            "current_difficulty": self.current_difficulty.value,
            "overall_accuracy": round(self._overall_window.accuracy, 2),
            "questions_answered": len(self._overall_window.records),
            "topic_accuracies": {
                topic: round(win.accuracy, 2)
                for topic, win in self._topic_windows.items()
            },
            "difficulty_history": [d.value for d in self.difficulty_history],
        }
