from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class UserAnalytics:
    user_id: str
    total_exams_taken: int
    average_score: float
    total_anomalies: int
    exams_passed: int
    exams_failed: int
    pass_rate: float
    score_trend: List[Dict]  # [{"exam_id": x, "score": y, "date": z}, ...]
    anomaly_breakdown: Dict[str, int]  # {"face_absent": x, "multiple_faces": y, ...}
    strongest_areas: List[str]
    weakest_areas: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)
