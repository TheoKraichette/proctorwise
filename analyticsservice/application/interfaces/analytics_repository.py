from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class AnalyticsRepository(ABC):
    @abstractmethod
    def get_exam_submissions(self, exam_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_user_submissions(self, user_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_exam_anomalies(self, exam_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_user_anomalies(self, user_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def get_platform_totals(self) -> Dict:
        pass

    @abstractmethod
    def get_daily_activity(self, days: int = 30) -> List[Dict]:
        pass

    @abstractmethod
    def get_hourly_activity(self, date: datetime) -> List[Dict]:
        pass

    @abstractmethod
    def get_recent_exams(self, limit: int = 10) -> List[Dict]:
        pass

    @abstractmethod
    def get_recent_anomalies(self, limit: int = 10) -> List[Dict]:
        pass

    @abstractmethod
    def get_top_performers(self, limit: int = 10) -> List[Dict]:
        pass
