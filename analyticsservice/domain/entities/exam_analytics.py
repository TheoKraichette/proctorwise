from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class ExamAnalytics:
    exam_id: str
    total_submissions: int
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float  # Percentage of students above passing threshold
    score_distribution: Dict[str, int]  # {"0-20": x, "21-40": y, ...}
    question_analytics: List[Dict]  # Per-question statistics
    average_completion_time: Optional[float] = None  # in minutes
    anomaly_summary: Optional[Dict[str, int]] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
