from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ReservationModel(Base):
    __tablename__ = "reservations"
    reservation_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    exam_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
