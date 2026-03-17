"""Performance analyzer - identify weak areas and score trends."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from scoremap.models import (
    AnswerRecord,
    Difficulty,
    ExamType,
    SessionResult,
    TopicPerformance,
    UserProfile,
)


class PerformanceAnalyzer:
    """Analyzes practice performance to identify weak areas and track trends.

    Capabilities:
    - Per-topic accuracy and timing analysis
    - Difficulty-level performance breakdown
    - Score trend detection (improving, declining, stable)
    - Weak area identification with prioritized recommendations
    """

    def __init__(self, profile: UserProfile) -> None:
        self.profile = profile

    @property
    def total_questions_attempted(self) -> int:
        return len(self.profile.all_answers)

    @property
    def overall_accuracy(self) -> float:
        if not self.profile.all_answers:
            return 0.0
        correct = sum(1 for a in self.profile.all_answers if a.is_correct)
        return correct / len(self.profile.all_answers)

    def analyze_by_topic(self) -> list[TopicPerformance]:
        """Break down performance by topic."""
        topic_data: dict[str, list[AnswerRecord]] = defaultdict(list)
        for answer in self.profile.all_answers:
            topic_data[answer.topic].append(answer)

        results: list[TopicPerformance] = []
        for topic, answers in topic_data.items():
            correct = sum(1 for a in answers if a.is_correct)
            total = len(answers)
            accuracy = correct / total if total > 0 else 0.0
            avg_time = (
                sum(a.time_spent_seconds for a in answers) / total if total > 0 else 0.0
            )

            # Difficulty breakdown
            diff_breakdown: dict[str, float] = {}
            for diff in Difficulty:
                diff_answers = [a for a in answers if a.difficulty == diff]
                if diff_answers:
                    diff_correct = sum(1 for a in diff_answers if a.is_correct)
                    diff_breakdown[diff.value] = round(diff_correct / len(diff_answers), 3)

            # Trend detection
            trend = self._detect_trend(answers)

            section = answers[0].section if answers else ""

            results.append(
                TopicPerformance(
                    topic=topic,
                    section=section,
                    total_attempted=total,
                    correct_count=correct,
                    accuracy=round(accuracy, 3),
                    average_time_seconds=round(avg_time, 1),
                    difficulty_breakdown=diff_breakdown,
                    trend=trend,
                )
            )

        # Sort by accuracy ascending (weakest first)
        results.sort(key=lambda tp: tp.accuracy)
        return results

    def analyze_by_section(self) -> dict[str, dict]:
        """Break down performance by exam section."""
        section_data: dict[str, list[AnswerRecord]] = defaultdict(list)
        for answer in self.profile.all_answers:
            section_data[answer.section].append(answer)

        results: dict[str, dict] = {}
        for section, answers in section_data.items():
            correct = sum(1 for a in answers if a.is_correct)
            total = len(answers)
            results[section] = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 3) if total else 0.0,
                "average_time": round(
                    sum(a.time_spent_seconds for a in answers) / total, 1
                )
                if total
                else 0.0,
            }
        return results

    def analyze_by_difficulty(self) -> dict[str, dict]:
        """Break down performance by difficulty level."""
        diff_data: dict[str, list[AnswerRecord]] = defaultdict(list)
        for answer in self.profile.all_answers:
            diff_data[answer.difficulty.value].append(answer)

        results: dict[str, dict] = {}
        for diff, answers in diff_data.items():
            correct = sum(1 for a in answers if a.is_correct)
            total = len(answers)
            results[diff] = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 3) if total else 0.0,
            }
        return results

    def identify_weak_areas(self, threshold: float = 0.60) -> list[TopicPerformance]:
        """Identify topics where accuracy falls below the threshold."""
        all_topics = self.analyze_by_topic()
        return [tp for tp in all_topics if tp.accuracy < threshold]

    def identify_strong_areas(self, threshold: float = 0.80) -> list[TopicPerformance]:
        """Identify topics where the user excels."""
        all_topics = self.analyze_by_topic()
        return [tp for tp in all_topics if tp.accuracy >= threshold]

    def get_score_trend(self) -> str:
        """Analyze overall trend across all sessions."""
        if len(self.profile.sessions) < 2:
            return "insufficient_data"
        accuracies = [s.accuracy for s in self.profile.sessions]
        return self._compute_trend(accuracies)

    def get_estimated_score(self) -> int | None:
        """Estimate a scaled score based on overall accuracy."""
        from scoremap.exams import get_exam_definition

        if not self.profile.all_answers:
            return None

        defn = get_exam_definition(self.profile.exam_type)
        low, high = defn.score_range
        score_range = high - low

        # Simple linear mapping from accuracy to score range
        estimated = low + int(self.overall_accuracy * score_range)
        return max(low, min(high, estimated))

    def get_summary(self) -> dict:
        """Produce a comprehensive performance summary."""
        return {
            "exam_type": self.profile.exam_type.value,
            "total_questions": self.total_questions_attempted,
            "overall_accuracy": round(self.overall_accuracy, 3),
            "estimated_score": self.get_estimated_score(),
            "score_trend": self.get_score_trend(),
            "sessions_completed": len(self.profile.sessions),
            "weak_areas": [
                {"topic": w.topic, "accuracy": w.accuracy}
                for w in self.identify_weak_areas()
            ],
            "strong_areas": [
                {"topic": s.topic, "accuracy": s.accuracy}
                for s in self.identify_strong_areas()
            ],
            "by_section": self.analyze_by_section(),
            "by_difficulty": self.analyze_by_difficulty(),
        }

    def _detect_trend(self, answers: list[AnswerRecord]) -> str:
        """Detect if performance on a topic is improving, declining, or stable."""
        if len(answers) < 4:
            return "stable"

        # Split into first half and second half
        mid = len(answers) // 2
        first_half = answers[:mid]
        second_half = answers[mid:]

        first_acc = sum(1 for a in first_half if a.is_correct) / len(first_half)
        second_acc = sum(1 for a in second_half if a.is_correct) / len(second_half)

        diff = second_acc - first_acc
        if diff > 0.15:
            return "improving"
        elif diff < -0.15:
            return "declining"
        return "stable"

    @staticmethod
    def _compute_trend(values: list[float]) -> str:
        """Compute trend direction from a series of values."""
        if len(values) < 2:
            return "stable"

        mid = len(values) // 2
        first_avg = sum(values[:mid]) / mid if mid else 0
        second_avg = sum(values[mid:]) / (len(values) - mid) if (len(values) - mid) else 0

        diff = second_avg - first_avg
        if diff > 0.10:
            return "improving"
        elif diff < -0.10:
            return "declining"
        return "stable"
