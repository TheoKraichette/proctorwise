from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class QuestionResult:
    question_id: str
    question_type: str
    user_answer: str
    correct_answer: Optional[str]
    is_correct: Optional[bool]
    score: float
    max_score: float
    feedback: Optional[str]


@dataclass
class GradingResult:
    submission_id: str
    user_id: str
    exam_id: str
    total_score: float
    max_score: float
    percentage: float
    graded_at: datetime
    question_results: List[QuestionResult] = field(default_factory=list)
    requires_manual_review: bool = False
    manual_review_questions: List[str] = field(default_factory=list)
    summary: Optional[Dict[str, int]] = None  # {"correct": x, "incorrect": y, "partial": z}
