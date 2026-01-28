from typing import Optional
from infrastructure.database.models import UserModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.user import User
from application.interfaces.user_repository import UserRepository

class SQLAlchemyUserRepository(UserRepository):
    def create(self, user: User) -> User:
        session = SessionLocal()
        try:
            db_user = UserModel(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                hashed_password=user.hashed_password,
                role=user.role,
                is_active=user.is_active
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return self._to_entity(db_user)
        finally:
            session.close()

    def get_by_id(self, user_id: str) -> Optional[User]:
        session = SessionLocal()
        try:
            db_user = session.query(UserModel).filter_by(user_id=user_id).first()
            return self._to_entity(db_user) if db_user else None
        finally:
            session.close()

    def get_by_email(self, email: str) -> Optional[User]:
        session = SessionLocal()
        try:
            db_user = session.query(UserModel).filter_by(email=email).first()
            return self._to_entity(db_user) if db_user else None
        finally:
            session.close()

    def _to_entity(self, db_user: UserModel) -> User:
        return User(
            user_id=db_user.user_id,
            name=db_user.name,
            email=db_user.email,
            role=db_user.role,
            hashed_password=db_user.hashed_password,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
