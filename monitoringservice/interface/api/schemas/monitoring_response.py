from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class MonitoringSessionResponse(BaseModel):
    session_id: str
    reservation_id: str
    user_id: str
    exam_id: str
    status: str
    started_at: datetime
    stopped_at: Optional[datetime] = None
    total_frames_processed: int
    anomaly_count: int


class AnomalyResponse(BaseModel):
    anomaly_id: str
    session_id: str
    anomaly_type: str
    severity: str
    detection_method: str
    confidence: float
    detected_at: datetime
    frame_path: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProcessFrameResponse(BaseModel):
    session_id: str
    frame_number: int
    anomalies_detected: List[AnomalyResponse]


class AnomalySummaryResponse(BaseModel):
    session_id: str
    total_anomalies: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_detection_method: Dict[str, int]
