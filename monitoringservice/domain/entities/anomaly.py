from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Anomaly:
    anomaly_id: str
    session_id: str
    anomaly_type: str  # "face_absent", "multiple_faces", "forbidden_object", "tab_change", "webcam_disabled"
    severity: str  # "low", "medium", "high", "critical"
    detection_method: str  # "rule", "ml", "hybrid"
    confidence: float  # 0.0 to 1.0
    detected_at: datetime
    frame_path: Optional[str] = None  # HDFS path to frame
    description: Optional[str] = None
    metadata: Optional[dict] = None
