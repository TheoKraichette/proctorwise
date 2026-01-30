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

    preference_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, unique=True, index=True)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    notification_types = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
