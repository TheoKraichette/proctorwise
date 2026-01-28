from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ExamSubmission:
    submission_id: str
    user_id: str
    exam_id: str
    reservation_id: str
    submitted_at: datetime
    status: str  # "submitted", "grading", "graded", "manual_review"
    total_score: Optional[float] = None
    max_score: Optional[float] = None
    percentage: Optional[float] = None
    graded_at: Optional[datetime] = None
    graded_by: Optional[str] = None  # "auto" or user_id
