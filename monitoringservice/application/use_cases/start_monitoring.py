from domain.entities.monitoring_session import MonitoringSession
from application.interfaces.monitoring_repository import MonitoringRepository
from application.interfaces.event_publisher import EventPublisher
import uuid
from datetime import datetime


class StartMonitoring:
    def __init__(self, repository: MonitoringRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(self, reservation_id: str, user_id: str, exam_id: str) -> MonitoringSession:
        existing = self.repository.get_active_session_by_reservation(reservation_id)
        if existing:
            raise ValueError(f"Active monitoring session already exists for reservation {reservation_id}")

        session_id = str(uuid.uuid4())
        session = MonitoringSession(
            session_id=session_id,
            reservation_id=reservation_id,
            user_id=user_id,
            exam_id=exam_id,
            status="active",
            started_at=datetime.utcnow(),
            total_frames_processed=0,
            anomaly_count=0
        )

        self.repository.create_session(session)

        await self.event_publisher.publish("monitoring_started", {
            "session_id": session_id,
            "reservation_id": reservation_id,
            "user_id": user_id,
            "exam_id": exam_id,
            "started_at": session.started_at.isoformat()
        })

        return session
