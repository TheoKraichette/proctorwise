from domain.entities.reservation import Reservation
from application.interfaces.reservation_repository import ReservationRepository
from application.interfaces.event_publisher import EventPublisher
import uuid
from datetime import datetime

class CreateReservation:
    def __init__(self, repository: ReservationRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(self, user_id: str, exam_id: str, start_time: datetime, end_time: datetime):
        reservation_id = str(uuid.uuid4())
        reservation = Reservation(
            reservation_id=reservation_id,
            user_id=user_id,
            exam_id=exam_id,
            start_time=start_time,
            end_time=end_time,
            status="scheduled"
        )
        self.repository.create(reservation)
        await self.event_publisher.publish("exam_scheduled", {
            "reservation_id": reservation_id,
            "user_id": user_id,
            "exam_id": exam_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        return reservation
