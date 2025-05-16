from abc import ABC, abstractmethod
from domain.entities.user import User

class UserRepository(ABC):
    @abstractmethod
    def create(self, user: User): pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> User: pass
