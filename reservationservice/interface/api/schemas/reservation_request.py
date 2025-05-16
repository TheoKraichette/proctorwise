from pydantic import BaseModel
from datetime import datetime

class ReservationCreateRequest(BaseModel):
    user_id: str
    exam_id: str
    start_time: datetime
    end_time: datetime
