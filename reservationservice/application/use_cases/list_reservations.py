from application.interfaces.reservation_repository import ReservationRepository
from typing import List
from domain.entities.reservation import Reservation

class ListReservationsByUser:
    def __init__(self, repository: ReservationRepository):
        self.repository = repository

    def execute(self, user_id: str) -> List[Reservation]:
        return self.repository.list_by_user(user_id)
