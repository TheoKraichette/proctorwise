from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.monitoring_session import MonitoringSession
from domain.entities.anomaly import Anomaly


class MonitoringRepository(ABC):
    @abstractmethod
    def create_session(self, session: MonitoringSession) -> None:
        pass

    @abstractmethod
    def get_session_by_id(self, session_id: str) -> Optional[MonitoringSession]:
        pass

    @abstractmethod
    def get_active_session_by_reservation(self, reservation_id: str) -> Optional[MonitoringSession]:
        pass

    @abstractmethod
    def update_session(self, session: MonitoringSession) -> None:
        pass

    @abstractmethod
    def create_anomaly(self, anomaly: Anomaly) -> None:
        pass

    @abstractmethod
    def get_anomalies_by_session(self, session_id: str) -> List[Anomaly]:
        pass

    @abstractmethod
    def get_anomaly_count_by_session(self, session_id: str, severity: Optional[str] = None) -> int:
        pass

    @abstractmethod
    def get_recent_anomalies(self, session_id: str, seconds: int = 60) -> List[Anomaly]:
        pass
