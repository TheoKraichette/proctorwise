import os
import bcrypt
from datetime import datetime, timedelta
from jose import jwt
from typing import Tuple
from domain.entities.user import User
from application.interfaces.user_repository import UserRepository

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "proctorwise_jwt_secret_change_in_prod")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = 24

class LoginUser:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def execute(self, email: str, password: str) -> Tuple[str, User]:
        # Get user by email
        user = self.repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
            raise ValueError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is deactivated")

        # Generate JWT token
        token = self._create_token(user)

        return token, user

    def _create_token(self, user: User) -> str:
        payload = {
            "sub": user.user_id,
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
