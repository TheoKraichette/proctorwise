from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Answer:
    answer_id: str
    submission_id: str
    question_id: str
    question_type: str  # "mcq", "essay", "short_answer", "true_false"
    user_answer: str
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    max_score: float = 1.0
    feedback: Optional[str] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None  # "auto" or user_id for manual review
