from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import numpy as np

from domain.entities.monitoring_session import MonitoringSession
from domain.entities.anomaly import Anomaly
from application.interfaces.monitoring_repository import MonitoringRepository
from application.interfaces.ml_detector import MLDetector
from application.interfaces.frame_storage import FrameStorage
from application.interfaces.event_publisher import EventPublisher


class ProcessFrame:
    FACE_ABSENT_THRESHOLD_SECONDS = 5
    FORBIDDEN_OBJECTS = ["cell phone", "phone", "book", "laptop", "tablet"]

    def __init__(
        self,
        repository: MonitoringRepository,
        ml_detector: MLDetector,
        frame_storage: FrameStorage,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.ml_detector = ml_detector
        self.frame_storage = frame_storage
        self.event_publisher = event_publisher
        self._face_absent_start: dict = {}

    async def execute(
        self,
        session_id: str,
        frame: np.ndarray,
        frame_number: int,
        browser_event: Optional[str] = None  # "tab_change", "webcam_disabled"
    ) -> List[Anomaly]:
        session = self.repository.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"Monitoring session {session_id} not found")

        if session.status != "active":
            raise ValueError(f"Monitoring session {session_id} is not active")

        frame_path = self.frame_storage.store_frame(session_id, frame_number, frame)

        detected_anomalies: List[Anomaly] = []

        if browser_event:
            anomaly = self._handle_browser_event(session_id, browser_event, frame_path)
            if anomaly:
                detected_anomalies.append(anomaly)

        faces = self.ml_detector.detect_faces(frame)
        face_anomalies = self._check_face_anomalies(session_id, faces, frame_path)
        detected_anomalies.extend(face_anomalies)

        objects = self.ml_detector.detect_objects(frame)
        object_anomalies = self._check_forbidden_objects(session_id, objects, frame_path)
        detected_anomalies.extend(object_anomalies)

        for anomaly in detected_anomalies:
            self.repository.create_anomaly(anomaly)
            await self._publish_anomaly_event(anomaly, session)

        await self._check_high_risk_alert(session)

        session.total_frames_processed = frame_number
        session.anomaly_count = self.repository.get_anomaly_count_by_session(session_id)
        self.repository.update_session(session)

        return detected_anomalies

    def _handle_browser_event(self, session_id: str, event: str, frame_path: str) -> Optional[Anomaly]:
        if event == "tab_change":
            return Anomaly(
                anomaly_id=str(uuid.uuid4()),
                session_id=session_id,
                anomaly_type="tab_change",
                severity="medium",
                detection_method="rule",
                confidence=1.0,
                detected_at=datetime.utcnow(),
                frame_path=frame_path,
                description="User changed browser tab during exam"
            )
        elif event == "webcam_disabled":
            return Anomaly(
                anomaly_id=str(uuid.uuid4()),
                session_id=session_id,
                anomaly_type="webcam_disabled",
                severity="critical",
                detection_method="rule",
                confidence=1.0,
                detected_at=datetime.utcnow(),
                frame_path=frame_path,
                description="Webcam was disabled during exam"
            )
        return None

    def _check_face_anomalies(self, session_id: str, faces: list, frame_path: str) -> List[Anomaly]:
        anomalies = []
        now = datetime.utcnow()

        if len(faces) == 0:
            if session_id not in self._face_absent_start:
                self._face_absent_start[session_id] = now
            elif (now - self._face_absent_start[session_id]).total_seconds() >= self.FACE_ABSENT_THRESHOLD_SECONDS:
                anomalies.append(Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    session_id=session_id,
                    anomaly_type="face_absent",
                    severity="high",
                    detection_method="rule",
                    confidence=1.0,
                    detected_at=now,
                    frame_path=frame_path,
                    description=f"No face detected for more than {self.FACE_ABSENT_THRESHOLD_SECONDS} seconds"
                ))
                self._face_absent_start[session_id] = now
        else:
            self._face_absent_start.pop(session_id, None)

        if len(faces) > 1:
            max_confidence = max(f.confidence for f in faces)
            anomalies.append(Anomaly(
                anomaly_id=str(uuid.uuid4()),
                session_id=session_id,
                anomaly_type="multiple_faces",
                severity="critical",
                detection_method="hybrid",
                confidence=max_confidence,
                detected_at=now,
                frame_path=frame_path,
                description=f"Detected {len(faces)} faces in frame",
                metadata={"face_count": len(faces)}
            ))

        return anomalies

    def _check_forbidden_objects(self, session_id: str, objects: list, frame_path: str) -> List[Anomaly]:
        anomalies = []
        now = datetime.utcnow()

        for obj in objects:
            if obj.label.lower() in [fo.lower() for fo in self.FORBIDDEN_OBJECTS]:
                anomalies.append(Anomaly(
                    anomaly_id=str(uuid.uuid4()),
                    session_id=session_id,
                    anomaly_type="forbidden_object",
                    severity="high",
                    detection_method="ml",
                    confidence=obj.confidence,
                    detected_at=now,
                    frame_path=frame_path,
                    description=f"Detected forbidden object: {obj.label}",
                    metadata={
                        "object_type": obj.label,
                        "bbox": obj.bbox
                    }
                ))

        return anomalies

    async def _publish_anomaly_event(self, anomaly: Anomaly, session: MonitoringSession):
        await self.event_publisher.publish("anomaly_detected", {
            "anomaly_id": anomaly.anomaly_id,
            "session_id": anomaly.session_id,
            "user_id": session.user_id,
            "exam_id": session.exam_id,
            "anomaly_type": anomaly.anomaly_type,
            "severity": anomaly.severity,
            "detection_method": anomaly.detection_method,
            "confidence": anomaly.confidence,
            "detected_at": anomaly.detected_at.isoformat(),
            "description": anomaly.description
        })

    async def _check_high_risk_alert(self, session: MonitoringSession):
        recent_anomalies = self.repository.get_recent_anomalies(session.session_id, seconds=60)
        critical_count = sum(1 for a in recent_anomalies if a.severity == "critical")

        if critical_count >= 3:
            await self.event_publisher.publish("high_risk_alert", {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "exam_id": session.exam_id,
                "reservation_id": session.reservation_id,
                "critical_anomalies_last_minute": critical_count,
                "alert_time": datetime.utcnow().isoformat(),
                "message": f"High risk detected: {critical_count} critical anomalies in the last minute"
            })
