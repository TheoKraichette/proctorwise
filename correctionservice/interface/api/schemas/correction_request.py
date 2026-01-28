from pydantic import BaseModel
from typing import List, Optional


class AnswerData(BaseModel):
    question_id: str
    question_type: str  # "mcq", "essay", "short_answer", "true_false"
    user_answer: str
    correct_answer: Optional[str] = None
    max_score: float = 1.0


class SubmitExamRequest(BaseModel):
    user_id: str
    exam_id: str
    reservation_id: str
    answers: List[AnswerData]


class ManualGradeRequest(BaseModel):
    score: float
    feedback: Optional[str] = None
    grader_id: str
