from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Reservation:
    reservation_id: str
    user_id: str
    exam_id: str
    start_time: datetime
    end_time: datetime
    status: str  # e.g. "scheduled", "cancelled", "confirmed"
    created_at: Optional[datetime] = None
