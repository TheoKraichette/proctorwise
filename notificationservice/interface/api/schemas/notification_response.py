from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    notification_type: str
    channel: str
    subject: str
    body: str
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UserPreferenceResponse(BaseModel):
    user_id: str
    email_enabled: bool
    websocket_enabled: bool
    notification_types: List[str]
