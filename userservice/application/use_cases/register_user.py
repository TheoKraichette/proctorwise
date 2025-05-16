from domain.entities.user import User
from application.interfaces.user_repository import UserRepository

class RegisterUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, user_data: dict):
        user = User(**user_data)
        self.repository.create(user)
        return user
