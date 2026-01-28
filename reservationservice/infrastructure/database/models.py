from sqlalchemy import Column, String, DateTime, Integer, Text, Float, ForeignKey
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


class QuestionModel(Base):
    __tablename__ = "questions"
    question_id = Column(String(36), primary_key=True)
    exam_id = Column(String(36), nullable=False, index=True)
    question_number = Column(Integer, nullable=False)
    question_type = Column(String(20), nullable=False)  # mcq, true_false, fill_blank
    question_text = Column(Text, nullable=False)
    option_a = Column(String(500), nullable=True)
    option_b = Column(String(500), nullable=True)
    option_c = Column(String(500), nullable=True)
    option_d = Column(String(500), nullable=True)
    correct_answer = Column(String(500), nullable=False)
    points = Column(Float, nullable=False, default=1.0)
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
