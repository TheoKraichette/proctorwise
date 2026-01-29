from domain.entities.reservation import Reservation
from application.interfaces.reservation_repository import ReservationRepository
from application.interfaces.exam_repository import ExamRepository
from application.interfaces.event_publisher import EventPublisher
import uuid
from datetime import datetime

class CreateReservation:
    def __init__(self, repository: ReservationRepository, event_publisher: EventPublisher, exam_repository: ExamRepository = None):
        self.repository = repository
        self.event_publisher = event_publisher
        self.exam_repository = exam_repository

    async def execute(self, user_id: str, exam_id: str, start_time: datetime, end_time: datetime, student_name: str = None):
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

        # Get exam details to include teacher_id
        teacher_id = None
        exam_title = None
        if self.exam_repository:
            exam = await self.exam_repository.get_by_id(exam_id)
            if exam:
                teacher_id = exam.teacher_id
                exam_title = exam.title

        await self.event_publisher.publish("exam_scheduled", {
            "reservation_id": reservation_id,
            "user_id": user_id,
            "student_name": student_name,
            "exam_id": exam_id,
            "exam_title": exam_title,
            "teacher_id": teacher_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        })
        return reservation
