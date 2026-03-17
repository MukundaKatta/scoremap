"""Exam definitions for standardized tests."""

from scoremap.exams.gmat import GMAT_DEFINITION, GMAT_QUESTIONS
from scoremap.exams.gre import GRE_DEFINITION, GRE_QUESTIONS
from scoremap.exams.sat import SAT_DEFINITION, SAT_QUESTIONS
from scoremap.models import ExamDefinition, ExamType, Question

EXAM_DEFINITIONS: dict[ExamType, ExamDefinition] = {
    ExamType.SAT: SAT_DEFINITION,
    ExamType.GRE: GRE_DEFINITION,
    ExamType.GMAT: GMAT_DEFINITION,
}

EXAM_QUESTIONS: dict[ExamType, list[Question]] = {
    ExamType.SAT: SAT_QUESTIONS,
    ExamType.GRE: GRE_QUESTIONS,
    ExamType.GMAT: GMAT_QUESTIONS,
}


def get_exam_definition(exam_type: ExamType) -> ExamDefinition:
    return EXAM_DEFINITIONS[exam_type]


def get_questions(exam_type: ExamType) -> list[Question]:
    return EXAM_QUESTIONS[exam_type]


def get_sections(exam_type: ExamType) -> list[str]:
    defn = get_exam_definition(exam_type)
    return [s.name for s in defn.sections]
