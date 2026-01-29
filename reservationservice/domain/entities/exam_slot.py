from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ExamSlot:
    slot_id: str
    exam_id: str
    start_time: datetime
    created_at: Optional[datetime] = None
