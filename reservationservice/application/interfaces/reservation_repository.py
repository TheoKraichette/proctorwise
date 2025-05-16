from abc import ABC, abstractmethod
from domain.entities.reservation import Reservation
from typing import List

class ReservationRepository(ABC):
    @abstractmethod
    def create(self, reservation: Reservation): pass

    @abstractmethod
    def get_by_id(self, reservation_id: str) -> Reservation: pass

    @abstractmethod
    def list_by_user(self, user_id: str) -> List[Reservation]: pass

    @abstractmethod
    def update(self, reservation: Reservation): pass
