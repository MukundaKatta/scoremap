"""Study planner - generate personalized study schedules."""

from __future__ import annotations

from datetime import datetime

from scoremap.analyzer import PerformanceAnalyzer
from scoremap.exams import get_exam_definition
from scoremap.models import (
    Difficulty,
    ExamType,
    StudyBlock,
    StudyPlan,
    TopicPerformance,
    UserProfile,
)


# Default study parameters
DEFAULT_WEEKLY_HOURS = 10
MINUTES_PER_QUESTION = 3
DAYS_PER_WEEK = 5


class StudyPlanner:
    """Generates personalized study schedules based on performance analysis.

    Strategy:
    - Allocate more time to weak areas (lower accuracy topics)
    - Gradually increase difficulty for improving topics
    - Ensure all sections get coverage, even strong ones
    - Distribute study across the week to avoid burnout
    """

    def __init__(
        self,
        profile: UserProfile,
        weekly_hours: float = DEFAULT_WEEKLY_HOURS,
    ) -> None:
        self.profile = profile
        self.weekly_hours = weekly_hours
        self.analyzer = PerformanceAnalyzer(profile)
        self.exam_def = get_exam_definition(profile.exam_type)

    def generate_plan(self, weeks: int = 4) -> StudyPlan:
        """Generate a multi-week study plan."""
        topic_performances = self.analyzer.analyze_by_topic()
        weak_areas = self.analyzer.identify_weak_areas()
        all_topics = self._get_all_topics()

        # Calculate time allocation per topic based on weakness
        topic_weights = self._compute_topic_weights(topic_performances, all_topics)
        daily_minutes = (self.weekly_hours * 60) / DAYS_PER_WEEK

        blocks: list[StudyBlock] = []
        day_counter = 0

        for week in range(weeks):
            for day_in_week in range(DAYS_PER_WEEK):
                day_counter += 1
                day_blocks = self._plan_day(
                    day=day_counter,
                    daily_minutes=daily_minutes,
                    topic_weights=topic_weights,
                    topic_performances=topic_performances,
                    week=week,
                    total_weeks=weeks,
                )
                blocks.extend(day_blocks)

        priority_topics = [w.topic for w in weak_areas[:5]] if weak_areas else []
        if not priority_topics:
            # If no data yet, prioritize by section importance
            priority_topics = [t for t in all_topics[:5]]

        return StudyPlan(
            exam_type=self.profile.exam_type,
            total_weeks=weeks,
            blocks=blocks,
            weekly_hours=self.weekly_hours,
            priority_topics=priority_topics,
        )

    def _get_all_topics(self) -> list[str]:
        """Get all topics from the exam definition."""
        topics: list[str] = []
        for section in self.exam_def.sections:
            topics.extend(section.topics)
        return topics

    def _get_section_for_topic(self, topic: str) -> str:
        """Find which section a topic belongs to."""
        for section in self.exam_def.sections:
            if topic in section.topics:
                return section.name
        return "general"

    def _compute_topic_weights(
        self,
        performances: list[TopicPerformance],
        all_topics: list[str],
    ) -> dict[str, float]:
        """Assign weights to topics - weaker topics get more study time.

        Weight formula:
        - No data: default weight of 1.0
        - Has data: weight = 1.5 - accuracy (so 40% accuracy -> 1.1 weight, 90% -> 0.6)
        - Minimum weight of 0.3 to ensure all topics get some coverage
        """
        perf_map = {tp.topic: tp for tp in performances}
        weights: dict[str, float] = {}

        for topic in all_topics:
            if topic in perf_map:
                accuracy = perf_map[topic].accuracy
                weight = max(0.3, 1.5 - accuracy)
            else:
                weight = 1.0  # Default for unseen topics
            weights[topic] = round(weight, 2)

        # Normalize so weights sum to 1
        total = sum(weights.values())
        if total > 0:
            weights = {t: w / total for t, w in weights.items()}

        return weights

    def _get_difficulty_for_week(
        self,
        topic: str,
        week: int,
        total_weeks: int,
        performances: list[TopicPerformance],
    ) -> Difficulty:
        """Determine appropriate difficulty for a topic in a given week.

        - Early weeks: start at current level or below
        - Middle weeks: current level
        - Later weeks: push to harder difficulty
        """
        perf_map = {tp.topic: tp for tp in performances}

        # Base difficulty from current performance
        if topic in perf_map:
            accuracy = perf_map[topic].accuracy
            if accuracy >= 0.80:
                base = Difficulty.HARD
            elif accuracy >= 0.50:
                base = Difficulty.MEDIUM
            else:
                base = Difficulty.EASY
        else:
            base = Difficulty.EASY

        # Adjust based on week progression
        progress = week / max(1, total_weeks - 1) if total_weeks > 1 else 0
        difficulty_order = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
        base_idx = difficulty_order.index(base)

        if progress > 0.7 and base_idx < 2:
            return difficulty_order[base_idx + 1]
        elif progress < 0.3 and base_idx > 0:
            return difficulty_order[max(0, base_idx - 1)]

        return base

    def _plan_day(
        self,
        day: int,
        daily_minutes: float,
        topic_weights: dict[str, float],
        topic_performances: list[TopicPerformance],
        week: int,
        total_weeks: int,
    ) -> list[StudyBlock]:
        """Plan study blocks for a single day."""
        blocks: list[StudyBlock] = []
        remaining_minutes = daily_minutes

        # Sort topics by weight (descending) so weak topics come first
        sorted_topics = sorted(topic_weights.items(), key=lambda x: -x[1])

        # Rotate topics across days to ensure variety
        topic_count = len(sorted_topics)
        if topic_count == 0:
            return blocks

        # Pick 2-3 topics per day, cycling through them
        topics_per_day = min(3, topic_count)
        start_idx = (day - 1) * topics_per_day % topic_count

        for i in range(topics_per_day):
            if remaining_minutes < 15:
                break

            idx = (start_idx + i) % topic_count
            topic, weight = sorted_topics[idx]
            section = self._get_section_for_topic(topic)

            # Allocate time proportional to weight
            block_minutes = max(15, int(daily_minutes * weight * topics_per_day))
            block_minutes = min(block_minutes, int(remaining_minutes))

            difficulty = self._get_difficulty_for_week(
                topic, week, total_weeks, topic_performances
            )

            question_count = max(1, block_minutes // MINUTES_PER_QUESTION)

            focus = self._get_focus_description(topic, difficulty, week, total_weeks)

            blocks.append(
                StudyBlock(
                    day=day,
                    topic=topic,
                    section=section,
                    focus=focus,
                    duration_minutes=block_minutes,
                    difficulty=difficulty,
                    question_count=question_count,
                )
            )

            remaining_minutes -= block_minutes

        return blocks

    def _get_focus_description(
        self, topic: str, difficulty: Difficulty, week: int, total_weeks: int
    ) -> str:
        """Generate a human-readable focus description."""
        progress = week / max(1, total_weeks - 1) if total_weeks > 1 else 0

        if progress < 0.3:
            phase = "Foundation building"
        elif progress < 0.7:
            phase = "Skill development"
        else:
            phase = "Test readiness"

        topic_display = topic.replace("_", " ").title()
        return f"{phase}: {topic_display} ({difficulty.value})"
