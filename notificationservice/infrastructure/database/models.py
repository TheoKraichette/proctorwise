from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NotificationModel(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)


class UserPreferenceModel(Base):
    __tablename__ = "user_preferences"

    user_id = Column(String(36), primary_key=True)
    email = Column(String(255), nullable=False)
    email_enabled = Column(Boolean, default=True)
    websocket_enabled = Column(Boolean, default=True)
    notification_types = Column(JSON, nullable=True)
    reminder_hours_before = Column(JSON, nullable=True)
