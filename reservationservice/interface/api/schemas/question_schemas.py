from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class QuestionCreateRequest(BaseModel):
    question_type: str = "mcq"  # mcq, true_false, fill_blank
    question_text: str
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_answer: str
    points: float = 1.0


class QuestionResponse(BaseModel):
    question_id: str
    exam_id: str
    question_number: int
    question_type: str
    question_text: str
    option_a: Optional[str]
    option_b: Optional[str]
    option_c: Optional[str]
    option_d: Optional[str]
    points: float
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuestionWithAnswerResponse(QuestionResponse):
    correct_answer: str


class BulkQuestionsRequest(BaseModel):
    questions: List[QuestionCreateRequest]
