from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class ExamAnalyticsResponse(BaseModel):
    exam_id: str
    total_submissions: int
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    score_distribution: Dict[str, int]
    question_analytics: List[Dict[str, Any]]
    average_completion_time: Optional[float] = None
    anomaly_summary: Optional[Dict[str, int]] = None
    generated_at: datetime


class UserAnalyticsResponse(BaseModel):
    user_id: str
    total_exams_taken: int
    average_score: float
    total_anomalies: int
    exams_passed: int
    exams_failed: int
    pass_rate: float
    score_trend: List[Dict[str, Any]]
    anomaly_breakdown: Dict[str, int]
    strongest_areas: List[str]
    weakest_areas: List[str]
    generated_at: datetime


class PlatformMetricsResponse(BaseModel):
    total_users: int
    total_exams: int
    total_submissions: int
    total_monitoring_sessions: int
    active_sessions_now: int
    exams_today: int
    submissions_today: int
    anomalies_today: int
    average_anomalies_per_exam: float
    system_health: Dict[str, str]
    hourly_activity: List[Dict[str, Any]]
    daily_trends: List[Dict[str, Any]]
    generated_at: datetime


class AlertResponse(BaseModel):
    level: str
    message: str
    type: str


class DashboardResponse(BaseModel):
    platform_metrics: PlatformMetricsResponse
    recent_exams: List[Dict[str, Any]]
    recent_anomalies: List[Dict[str, Any]]
    top_performers: List[Dict[str, Any]]
    alerts: List[AlertResponse]
    generated_at: datetime
