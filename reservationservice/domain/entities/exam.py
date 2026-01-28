from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Exam:
    exam_id: str
    title: str
    teacher_id: str
    duration_minutes: int
    description: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
