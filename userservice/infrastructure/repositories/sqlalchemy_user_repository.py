from infrastructure.database.models import UserModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.user import User
from application.interfaces.user_repository import UserRepository

class SQLAlchemyUserRepository(UserRepository):
    def create(self, user: User):
        session = SessionLocal()
        db_user = UserModel(**user.__dict__)
        session.add(db_user)
        session.commit()
        session.close()

    def get_by_id(self, user_id: str):
        session = SessionLocal()
        user = session.query(UserModel).filter_by(user_id=user_id).first()
        session.close()
        return User(**user.__dict__) if user else None
