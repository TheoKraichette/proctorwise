from application.interfaces.user_repository import UserRepository

class GetUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, user_id: str):
        return self.repository.get_by_id(user_id)
