from domain.entities.reservation import Reservation
from application.interfaces.reservation_repository import ReservationRepository
from application.interfaces.event_publisher import EventPublisher

class CancelReservation:
    def __init__(self, repository: ReservationRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(self, reservation_id: str):
        reservation = self.repository.get_by_id(reservation_id)
        if reservation is None:
            raise ValueError("Reservation not found")
        reservation.status = "cancelled"
        self.repository.update(reservation)
        await self.event_publisher.publish("exam_cancelled", {
            "reservation_id": reservation_id,
            "user_id": reservation.user_id,
            "exam_id": reservation.exam_id,
        })
        return reservation
