from pydantic import BaseModel
from typing import Optional


class StartMonitoringRequest(BaseModel):
    reservation_id: str
    user_id: str
    exam_id: str


class ProcessFrameRequest(BaseModel):
    frame_data: str  # Base64 encoded frame
    frame_number: int
    browser_event: Optional[str] = None  # "tab_change", "webcam_disabled"
