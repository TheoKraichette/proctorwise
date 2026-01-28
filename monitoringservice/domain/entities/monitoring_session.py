from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MonitoringSession:
    session_id: str
    reservation_id: str
    user_id: str
    exam_id: str
    status: str  # "active", "stopped", "paused"
    started_at: datetime
    stopped_at: Optional[datetime] = None
    total_frames_processed: int = 0
    anomaly_count: int = 0
