from sqlalchemy import Column, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ExamSubmissionModel(Base):
    __tablename__ = "exam_submissions"

    submission_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    exam_id = Column(String(36), nullable=False, index=True)
    reservation_id = Column(String(36), nullable=False, index=True)
    submitted_at = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    total_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(String(36), nullable=True)


class AnswerModel(Base):
    __tablename__ = "answers"

    answer_id = Column(String(36), primary_key=True)
    submission_id = Column(String(36), nullable=False, index=True)
    question_id = Column(String(36), nullable=False, index=True)
    question_type = Column(String(20), nullable=False)
    user_answer = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=False, default=1.0)
    feedback = Column(Text, nullable=True)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(String(36), nullable=True)
