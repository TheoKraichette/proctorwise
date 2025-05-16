from pydantic import BaseModel
from datetime import datetime

class ReservationResponse(BaseModel):
    reservation_id: str
    user_id: str
    exam_id: str
    start_time: datetime
    end_time: datetime
    status: str
