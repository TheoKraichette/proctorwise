from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PlatformMetrics:
    total_users: int
    total_exams: int
    total_submissions: int
    total_monitoring_sessions: int
    active_sessions_now: int
    exams_today: int
    submissions_today: int
    anomalies_today: int
    average_anomalies_per_exam: float
    system_health: Dict[str, str]  # {"database": "healthy", "kafka": "healthy", ...}
    hourly_activity: List[Dict]  # [{"hour": 0, "sessions": x, "submissions": y}, ...]
    daily_trends: List[Dict]  # [{"date": "2024-01-01", "exams": x, "users": y}, ...]
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DashboardData:
    platform_metrics: PlatformMetrics
    recent_exams: List[Dict]
    recent_anomalies: List[Dict]
    top_performers: List[Dict]
    alerts: List[Dict]
    generated_at: datetime = field(default_factory=datetime.utcnow)
