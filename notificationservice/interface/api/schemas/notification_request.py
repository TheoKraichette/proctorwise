from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SendNotificationRequest(BaseModel):
    user_id: str
    notification_type: str
    subject: str
    body: str
    channel: str = "both"  # "email", "websocket", "both"
    metadata: Optional[Dict[str, Any]] = None


class UpdatePreferenceRequest(BaseModel):
    email: str
    email_enabled: bool = True
    websocket_enabled: bool = True
    notification_types: List[str] = ["exam_reminder", "anomaly_detected", "grade_ready", "high_risk_alert"]
    reminder_hours_before: List[int] = [24, 1]
