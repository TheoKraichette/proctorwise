from fastapi import APIRouter, HTTPException
from application.use_cases.create_reservation import CreateReservation
from application.use_cases.cancel_reservation import CancelReservation
from application.use_cases.list_reservations import ListReservationsByUser
from infrastructure.repositories.sqlalchemy_reservation_repository import SQLAlchemyReservationRepository
from infrastructure.events.kafka_publisher import KafkaEventPublisher
from interface.api.schemas.reservation_request import ReservationCreateRequest
from interface.api.schemas.reservation_response import ReservationResponse
from typing import List

router = APIRouter(prefix="/reservations", tags=["Reservations"])

repo = SQLAlchemyReservationRepository()
kafka_publisher = KafkaEventPublisher(bootstrap_servers="localhost:9092")

@router.post("/", response_model=ReservationResponse)
async def create_reservation(request: ReservationCreateRequest):
    use_case = CreateReservation(repo, kafka_publisher)
    reservation = await use_case.execute(
        request.user_id,
        request.exam_id,
        request.start_time,
        request.end_time
    )
    return ReservationResponse(**reservation.__dict__)

@router.delete("/{reservation_id}", response_model=ReservationResponse)
async def cancel_reservation(reservation_id: str):
    use_case = CancelReservation(repo, kafka_publisher)
    try:
        reservation = await use_case.execute(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ReservationResponse(**reservation.__dict__)

@router.get("/user/{user_id}", response_model=List[ReservationResponse])
def list_reservations(user_id: str):
    use_case = ListReservationsByUser(repo)
    reservations = use_case.execute(user_id)
    return [ReservationResponse(**r.__dict__) for r in reservations]
