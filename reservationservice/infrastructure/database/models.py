from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ReservationModel(Base):
    __tablename__ = "reservations"
    reservation_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    exam_id = Column(String(36), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default='scheduled')
    created_at = Column(DateTime, default=datetime.utcnow)
