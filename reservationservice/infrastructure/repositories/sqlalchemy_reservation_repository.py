from typing import Optional, List
from infrastructure.database.models import ReservationModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.reservation import Reservation
from application.interfaces.reservation_repository import ReservationRepository

class SQLAlchemyReservationRepository(ReservationRepository):

    def create(self, reservation: Reservation) -> Reservation:
        session = SessionLocal()
        try:
            db_reservation = ReservationModel(
                reservation_id=reservation.reservation_id,
                user_id=reservation.user_id,
                exam_id=reservation.exam_id,
                start_time=reservation.start_time,
                end_time=reservation.end_time,
                status=reservation.status
            )
            session.add(db_reservation)
            session.commit()
            session.refresh(db_reservation)
            return self._to_entity(db_reservation)
        finally:
            session.close()

    def get_by_id(self, reservation_id: str) -> Optional[Reservation]:
        session = SessionLocal()
        try:
            res = session.query(ReservationModel).filter_by(reservation_id=reservation_id).first()
            return self._to_entity(res) if res else None
        finally:
            session.close()

    def list_by_user(self, user_id: str) -> List[Reservation]:
        session = SessionLocal()
        try:
            results = session.query(ReservationModel).filter_by(user_id=user_id).all()
            return [self._to_entity(r) for r in results]
        finally:
            session.close()

    def list_by_exam(self, exam_id: str) -> List[Reservation]:
        session = SessionLocal()
        try:
            results = session.query(ReservationModel).filter_by(exam_id=exam_id).all()
            return [self._to_entity(r) for r in results]
        finally:
            session.close()

    def get_all(self) -> List[Reservation]:
        session = SessionLocal()
        try:
            results = session.query(ReservationModel).order_by(ReservationModel.created_at.desc()).all()
            return [self._to_entity(r) for r in results]
        finally:
            session.close()

    def update(self, reservation: Reservation) -> Optional[Reservation]:
        session = SessionLocal()
        try:
            db_res = session.query(ReservationModel).filter_by(reservation_id=reservation.reservation_id).first()
            if db_res:
                db_res.status = reservation.status
                db_res.start_time = reservation.start_time
                db_res.end_time = reservation.end_time
                session.commit()
                session.refresh(db_res)
                return self._to_entity(db_res)
            return None
        finally:
            session.close()

    def _to_entity(self, db_reservation: ReservationModel) -> Reservation:
        return Reservation(
            reservation_id=db_reservation.reservation_id,
            user_id=db_reservation.user_id,
            exam_id=db_reservation.exam_id,
            start_time=db_reservation.start_time,
            end_time=db_reservation.end_time,
            status=db_reservation.status,
            created_at=db_reservation.created_at
        )
