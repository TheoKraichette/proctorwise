from sqlalchemy import Column, String, DateTime, Integer, Float, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MonitoringSessionModel(Base):
    __tablename__ = "monitoring_sessions"

    session_id = Column(String(36), primary_key=True)
    reservation_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    exam_id = Column(String(36), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    stopped_at = Column("ended_at", DateTime, nullable=True)
    total_frames_processed = Column(Integer, default=0)
    anomaly_count = Column(Integer, default=0)


class AnomalyModel(Base):
    __tablename__ = "anomalies"

    anomaly_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    detection_method = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    detected_at = Column(DateTime, nullable=False, index=True)
    frame_path = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    extra_data = Column("metadata", JSON, nullable=True)
