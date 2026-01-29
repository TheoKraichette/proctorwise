from typing import List, Optional
from datetime import datetime, timedelta

from infrastructure.database.models import MonitoringSessionModel, AnomalyModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.monitoring_session import MonitoringSession
from domain.entities.anomaly import Anomaly
from application.interfaces.monitoring_repository import MonitoringRepository


def _to_monitoring_session(r: MonitoringSessionModel) -> MonitoringSession:
    return MonitoringSession(
        session_id=r.session_id,
        reservation_id=r.reservation_id,
        user_id=r.user_id,
        exam_id=r.exam_id,
        status=r.status,
        started_at=r.started_at,
        stopped_at=r.stopped_at,
        total_frames_processed=r.total_frames_processed,
        anomaly_count=r.anomaly_count
    )


def _to_anomaly(r: AnomalyModel) -> Anomaly:
    return Anomaly(
        anomaly_id=r.anomaly_id,
        session_id=r.session_id,
        anomaly_type=r.anomaly_type,
        severity=r.severity,
        detection_method=r.detection_method,
        confidence=r.confidence,
        detected_at=r.detected_at,
        frame_path=r.frame_path,
        description=r.description,
        metadata=r.extra_data
    )


class SQLAlchemyMonitoringRepository(MonitoringRepository):

    def create_session(self, session: MonitoringSession) -> None:
        db_session = SessionLocal()
        try:
            db_monitoring = MonitoringSessionModel(
                session_id=session.session_id,
                reservation_id=session.reservation_id,
                user_id=session.user_id,
                exam_id=session.exam_id,
                status=session.status,
                started_at=session.started_at,
                stopped_at=session.stopped_at,
                total_frames_processed=session.total_frames_processed,
                anomaly_count=session.anomaly_count
            )
            db_session.add(db_monitoring)
            db_session.commit()
        finally:
            db_session.close()

    def get_session_by_id(self, session_id: str) -> Optional[MonitoringSession]:
        db_session = SessionLocal()
        try:
            result = db_session.query(MonitoringSessionModel).filter_by(session_id=session_id).first()
            if not result:
                return None
            return _to_monitoring_session(result)
        finally:
            db_session.close()

    def get_active_session_by_reservation(self, reservation_id: str) -> Optional[MonitoringSession]:
        db_session = SessionLocal()
        try:
            result = db_session.query(MonitoringSessionModel).filter_by(
                reservation_id=reservation_id,
                status="active"
            ).first()
            if not result:
                return None
            return _to_monitoring_session(result)
        finally:
            db_session.close()

    def update_session(self, session: MonitoringSession) -> None:
        db_session = SessionLocal()
        try:
            db_monitoring = db_session.query(MonitoringSessionModel).filter_by(
                session_id=session.session_id
            ).first()
            if db_monitoring:
                db_monitoring.status = session.status
                db_monitoring.stopped_at = session.stopped_at
                db_monitoring.total_frames_processed = session.total_frames_processed
                db_monitoring.anomaly_count = session.anomaly_count
                db_session.commit()
        finally:
            db_session.close()

    def create_anomaly(self, anomaly: Anomaly) -> None:
        db_session = SessionLocal()
        try:
            db_anomaly = AnomalyModel(
                anomaly_id=anomaly.anomaly_id,
                session_id=anomaly.session_id,
                anomaly_type=anomaly.anomaly_type,
                severity=anomaly.severity,
                detection_method=anomaly.detection_method,
                confidence=anomaly.confidence,
                detected_at=anomaly.detected_at,
                frame_path=anomaly.frame_path,
                description=anomaly.description,
                extra_data=anomaly.metadata
            )
            db_session.add(db_anomaly)
            db_session.commit()
        finally:
            db_session.close()

    def get_anomalies_by_session(self, session_id: str) -> List[Anomaly]:
        db_session = SessionLocal()
        try:
            results = db_session.query(AnomalyModel).filter_by(session_id=session_id).all()
            return [_to_anomaly(r) for r in results]
        finally:
            db_session.close()

    def get_anomaly_count_by_session(self, session_id: str, severity: Optional[str] = None) -> int:
        db_session = SessionLocal()
        try:
            query = db_session.query(AnomalyModel).filter_by(session_id=session_id)
            if severity:
                query = query.filter_by(severity=severity)
            return query.count()
        finally:
            db_session.close()

    def get_all_sessions(self) -> List[MonitoringSession]:
        db_session = SessionLocal()
        try:
            results = db_session.query(MonitoringSessionModel).order_by(
                MonitoringSessionModel.started_at.desc()
            ).all()
            return [_to_monitoring_session(r) for r in results]
        finally:
            db_session.close()

    def get_recent_anomalies(self, session_id: str, seconds: int = 60) -> List[Anomaly]:
        db_session = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=seconds)
            results = db_session.query(AnomalyModel).filter(
                AnomalyModel.session_id == session_id,
                AnomalyModel.detected_at >= cutoff_time
            ).all()
            return [_to_anomaly(r) for r in results]
        finally:
            db_session.close()
