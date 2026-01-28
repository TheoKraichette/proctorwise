from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class AnswerResponse(BaseModel):
    answer_id: str
    submission_id: str
    question_id: str
    question_type: str
    user_answer: str
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    max_score: float
    feedback: Optional[str] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None


class SubmissionResponse(BaseModel):
    submission_id: str
    user_id: str
    exam_id: str
    reservation_id: str
    submitted_at: datetime
    status: str
    total_score: Optional[float] = None
    max_score: Optional[float] = None
    percentage: Optional[float] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None


class QuestionResultResponse(BaseModel):
    question_id: str
    question_type: str
    user_answer: str
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: float
    max_score: float
    feedback: Optional[str] = None


class GradingResultResponse(BaseModel):
    submission_id: str
    user_id: str
    exam_id: str
    total_score: float
    max_score: float
    percentage: float
    graded_at: datetime
    question_results: List[QuestionResultResponse]
    requires_manual_review: bool
    manual_review_questions: List[str]
    summary: Optional[Dict[str, int]] = None


class SubmissionDetailResponse(BaseModel):
    submission: SubmissionResponse
    answers: List[AnswerResponse]
    summary: Dict[str, int]
