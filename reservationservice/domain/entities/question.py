from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Question:
    question_id: str
    exam_id: str
    question_number: int
    question_type: str  # mcq, true_false, fill_blank
    question_text: str
    correct_answer: str
    points: float = 1.0
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    created_at: Optional[datetime] = None
