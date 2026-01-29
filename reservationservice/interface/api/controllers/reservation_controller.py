import os
from fastapi import APIRouter, HTTPException
from application.use_cases.create_reservation import CreateReservation
from application.use_cases.cancel_reservation import CancelReservation
from application.use_cases.list_reservations import ListReservationsByUser
from infrastructure.repositories.sqlalchemy_reservation_repository import SQLAlchemyReservationRepository
from infrastructure.repositories.sqlalchemy_exam_repository import SQLAlchemyExamRepository
from infrastructure.events.kafka_publisher import KafkaEventPublisher
from interface.api.schemas.reservation_request import ReservationCreateRequest
from interface.api.schemas.reservation_response import ReservationResponse
from typing import List

router = APIRouter(prefix="/reservations", tags=["Reservations"])

repo = SQLAlchemyReservationRepository()
exam_repo = SQLAlchemyExamRepository()
kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
kafka_publisher = KafkaEventPublisher(bootstrap_servers=kafka_bootstrap)

@router.post("/", response_model=ReservationResponse)
async def create_reservation(request: ReservationCreateRequest):
    use_case = CreateReservation(repo, kafka_publisher, exam_repo)
    reservation = await use_case.execute(
        request.user_id,
        request.exam_id,
        request.start_time,
        request.end_time,
        request.student_name
    )
    return ReservationResponse(
        reservation_id=reservation.reservation_id,
        user_id=reservation.user_id,
        exam_id=reservation.exam_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status=reservation.status,
        created_at=reservation.created_at
    )

@router.delete("/{reservation_id}", response_model=ReservationResponse)
async def cancel_reservation(reservation_id: str):
    use_case = CancelReservation(repo, kafka_publisher)
    try:
        reservation = await use_case.execute(reservation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ReservationResponse(
        reservation_id=reservation.reservation_id,
        user_id=reservation.user_id,
        exam_id=reservation.exam_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status=reservation.status,
        created_at=reservation.created_at
    )

@router.get("/all", response_model=List[ReservationResponse])
def list_all_reservations():
    """List all reservations (admin only)"""
    reservations = repo.get_all()
    return [ReservationResponse(
        reservation_id=r.reservation_id,
        user_id=r.user_id,
        exam_id=r.exam_id,
        start_time=r.start_time,
        end_time=r.end_time,
        status=r.status,
        created_at=r.created_at
    ) for r in reservations]

@router.get("/user/{user_id}", response_model=List[ReservationResponse])
def list_reservations(user_id: str):
    use_case = ListReservationsByUser(repo)
    reservations = use_case.execute(user_id)
    return [ReservationResponse(
        reservation_id=r.reservation_id,
        user_id=r.user_id,
        exam_id=r.exam_id,
        start_time=r.start_time,
        end_time=r.end_time,
        status=r.status,
        created_at=r.created_at
    ) for r in reservations]

@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: str):
    reservation = repo.get_by_id(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return ReservationResponse(
        reservation_id=reservation.reservation_id,
        user_id=reservation.user_id,
        exam_id=reservation.exam_id,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        status=reservation.status,
        created_at=reservation.created_at
    )

@router.patch("/{reservation_id}/status")
def update_reservation_status(reservation_id: str, status: str):
    reservation = repo.get_by_id(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    reservation.status = status
    updated = repo.update(reservation)
    return ReservationResponse(
        reservation_id=updated.reservation_id,
        user_id=updated.user_id,
        exam_id=updated.exam_id,
        start_time=updated.start_time,
        end_time=updated.end_time,
        status=updated.status,
        created_at=updated.created_at
    )
