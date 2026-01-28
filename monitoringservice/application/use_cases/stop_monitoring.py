from domain.entities.monitoring_session import MonitoringSession
from application.interfaces.monitoring_repository import MonitoringRepository
from application.interfaces.event_publisher import EventPublisher
from datetime import datetime


class StopMonitoring:
    def __init__(self, repository: MonitoringRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(self, session_id: str) -> MonitoringSession:
        session = self.repository.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Monitoring session {session_id} not found")

        if session.status != "active":
            raise ValueError(f"Monitoring session {session_id} is not active")

        session.status = "stopped"
        session.stopped_at = datetime.utcnow()

        self.repository.update_session(session)

        anomalies = self.repository.get_anomalies_by_session(session_id)

        await self.event_publisher.publish("monitoring_stopped", {
            "session_id": session_id,
            "reservation_id": session.reservation_id,
            "user_id": session.user_id,
            "exam_id": session.exam_id,
            "started_at": session.started_at.isoformat(),
            "stopped_at": session.stopped_at.isoformat(),
            "total_frames_processed": session.total_frames_processed,
            "total_anomalies": len(anomalies),
            "anomaly_summary": {
                "critical": sum(1 for a in anomalies if a.severity == "critical"),
                "high": sum(1 for a in anomalies if a.severity == "high"),
                "medium": sum(1 for a in anomalies if a.severity == "medium"),
                "low": sum(1 for a in anomalies if a.severity == "low")
            }
        })

        return session
