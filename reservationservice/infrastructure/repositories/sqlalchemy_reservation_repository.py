from infrastructure.database.models import ReservationModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.reservation import Reservation
from application.interfaces.reservation_repository import ReservationRepository

class SQLAlchemyReservationRepository(ReservationRepository):

    def create(self, reservation: Reservation):
        session = SessionLocal()
        db_reservation = ReservationModel(**reservation.__dict__)
        session.add(db_reservation)
        session.commit()
        session.close()

    def get_by_id(self, reservation_id: str):
        session = SessionLocal()
        res = session.query(ReservationModel).filter_by(reservation_id=reservation_id).first()
        session.close()
        return Reservation(**res.__dict__) if res else None

    def list_by_user(self, user_id: str):
        session = SessionLocal()
        results = session.query(ReservationModel).filter_by(user_id=user_id).all()
        session.close()
        return [Reservation(**r.__dict__) for r in results]

    def update(self, reservation: Reservation):
        session = SessionLocal()
        db_res = session.query(ReservationModel).filter_by(reservation_id=reservation.reservation_id).first()
        if db_res:
            db_res.status = reservation.status
            db_res.start_time = reservation.start_time
            db_res.end_time = reservation.end_time
            session.commit()
        session.close()
