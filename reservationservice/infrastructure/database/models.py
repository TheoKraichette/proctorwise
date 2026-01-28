from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ExamModel(Base):
    __tablename__ = "exams"
    exam_id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    teacher_id = Column(String(36), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)


class ReservationModel(Base):
    __tablename__ = "reservations"
    reservation_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    exam_id = Column(String(36), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default='scheduled')
    created_at = Column(DateTime, default=datetime.utcnow)
