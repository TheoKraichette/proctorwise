from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserPreference:
    user_id: str
    email_enabled: bool = True
    websocket_enabled: bool = True
    notification_types: List[str] = field(default_factory=lambda: [
        "exam_reminder",
        "anomaly_detected",
        "grade_ready",
        "high_risk_alert"
    ])
    preference_id: Optional[str] = None
