"""Core data models for SCOREMAP."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExamType(str, Enum):
    SAT = "sat"
    GRE = "gre"
    GMAT = "gmat"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    GRID_IN = "grid_in"
    TEXT_ENTRY = "text_entry"


class Question(BaseModel):
    """A single practice question."""

    id: str
    exam_type: ExamType
    section: str
    topic: str
    difficulty: Difficulty
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    text: str
    choices: list[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str = ""
    time_estimate_seconds: int = 90


class AnswerRecord(BaseModel):
    """Record of a user's answer to a question."""

    question_id: str
    exam_type: ExamType
    section: str
    topic: str
    difficulty: Difficulty
    user_answer: str
    correct_answer: str
    is_correct: bool
    time_spent_seconds: float
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionResult(BaseModel):
    """Results from a complete practice session."""

    exam_type: ExamType
    section: str
    answers: list[AnswerRecord]
    start_time: datetime
    end_time: datetime
    total_questions: int
    correct_count: int
    accuracy: float
    average_time_seconds: float

    @property
    def score_percentage(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.correct_count / self.total_questions) * 100


class TopicPerformance(BaseModel):
    """Performance metrics for a specific topic."""

    topic: str
    section: str
    total_attempted: int = 0
    correct_count: int = 0
    accuracy: float = 0.0
    average_time_seconds: float = 0.0
    difficulty_breakdown: dict[str, float] = Field(default_factory=dict)
    trend: str = "stable"  # improving, declining, stable


class ExamSection(BaseModel):
    """Definition of an exam section."""

    name: str
    topics: list[str]
    time_limit_minutes: int
    total_questions: int
    description: str = ""


class ExamDefinition(BaseModel):
    """Full exam definition."""

    exam_type: ExamType
    name: str
    sections: list[ExamSection]
    score_range: tuple[int, int]
    description: str = ""


class StudyBlock(BaseModel):
    """A single study block in a plan."""

    day: int
    topic: str
    section: str
    focus: str
    duration_minutes: int
    difficulty: Difficulty
    question_count: int


class StudyPlan(BaseModel):
    """A personalized study plan."""

    exam_type: ExamType
    total_weeks: int
    blocks: list[StudyBlock]
    weekly_hours: float
    priority_topics: list[str]
    created_at: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """Tracks cumulative user performance."""

    exam_type: ExamType
    sessions: list[SessionResult] = Field(default_factory=list)
    all_answers: list[AnswerRecord] = Field(default_factory=list)
    target_score: Optional[int] = None
    exam_date: Optional[datetime] = None
