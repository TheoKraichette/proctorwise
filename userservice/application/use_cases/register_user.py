import uuid
import bcrypt
from domain.entities.user import User
from application.interfaces.user_repository import UserRepository

class RegisterUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, name: str, email: str, password: str, role: str = "student") -> User:
        # Check if email already exists
        existing_user = self.repository.get_by_email(email)
        if existing_user:
            raise ValueError("Email already registered")

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user entity
        user = User(
            user_id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            hashed_password=hashed_password,
            is_active=True
        )

        # Save to repository
        return self.repository.create(user)
