from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Notification:
    notification_id: str
    user_id: str
    notification_type: str  # "exam_reminder", "anomaly_detected", "grade_ready", "high_risk_alert"
    channel: str  # "email", "websocket", "both"
    subject: str
    body: str
    status: str  # "pending", "sent", "failed"
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
