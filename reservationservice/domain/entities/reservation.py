from dataclasses import dataclass
from datetime import datetime

@dataclass
class Reservation:
    reservation_id: str
    user_id: str
    exam_id: str
    start_time: datetime
    end_time: datetime
    status: str  # e.g. "scheduled", "cancelled", "confirmed"
