from typing import List, Optional
from application.interfaces.monitoring_repository import MonitoringRepository
from domain.entities.anomaly import Anomaly


class GetAnomalies:
    def __init__(self, repository: MonitoringRepository):
        self.repository = repository

    def execute(
        self,
        session_id: str,
        severity: Optional[str] = None
    ) -> List[Anomaly]:
        session = self.repository.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Monitoring session {session_id} not found")

        anomalies = self.repository.get_anomalies_by_session(session_id)

        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]

        return sorted(anomalies, key=lambda a: a.detected_at, reverse=True)


class GetAnomalySummary:
    def __init__(self, repository: MonitoringRepository):
        self.repository = repository

    def execute(self, session_id: str) -> dict:
        session = self.repository.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Monitoring session {session_id} not found")

        anomalies = self.repository.get_anomalies_by_session(session_id)

        summary = {
            "session_id": session_id,
            "total_anomalies": len(anomalies),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "by_type": {},
            "by_detection_method": {
                "rule": 0,
                "ml": 0,
                "hybrid": 0
            }
        }

        for anomaly in anomalies:
            summary["by_severity"][anomaly.severity] = summary["by_severity"].get(anomaly.severity, 0) + 1
            summary["by_type"][anomaly.anomaly_type] = summary["by_type"].get(anomaly.anomaly_type, 0) + 1
            summary["by_detection_method"][anomaly.detection_method] = summary["by_detection_method"].get(anomaly.detection_method, 0) + 1

        return summary
