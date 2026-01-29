import base64
import os
from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import cv2
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from application.use_cases.start_monitoring import StartMonitoring
from application.use_cases.stop_monitoring import StopMonitoring
from application.use_cases.process_frame import ProcessFrame
from application.use_cases.detect_anomalies import GetAnomalies, GetAnomalySummary
from infrastructure.repositories.sqlalchemy_monitoring_repository import SQLAlchemyMonitoringRepository
from infrastructure.events.kafka_publisher import KafkaEventPublisher
from infrastructure.ml.object_detector import HybridDetector
from infrastructure.storage.hdfs_frame_storage import HDFSFrameStorage, LocalFrameStorage
from interface.api.schemas.monitoring_request import StartMonitoringRequest, ProcessFrameRequest
from interface.api.schemas.monitoring_response import (
    MonitoringSessionResponse,
    AnomalyResponse,
    ProcessFrameResponse,
    AnomalySummaryResponse
)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

repo = SQLAlchemyMonitoringRepository()
kafka_publisher = KafkaEventPublisher(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
)
ml_detector = HybridDetector()
frame_storage = LocalFrameStorage(base_path=os.getenv("FRAME_STORAGE_PATH", "./local_storage")) if os.getenv("USE_LOCAL_STORAGE") else HDFSFrameStorage()

# Singleton ProcessFrame to preserve _face_absent_start state across requests
process_frame_use_case = ProcessFrame(repo, ml_detector, frame_storage, kafka_publisher)

active_websockets: dict = {}
live_view_websockets: dict = {}  # session_id -> [WebSocket]


@router.get("/sessions", response_model=List[MonitoringSessionResponse])
def list_sessions(status: Optional[str] = None):
    sessions = repo.get_all_sessions()
    # Auto-stop stale sessions (active for more than 3 hours = orphaned)
    now = datetime.utcnow()
    for s in sessions:
        if s.status == "active" and s.started_at and (now - s.started_at) > timedelta(hours=3):
            s.status = "stopped"
            s.stopped_at = now
            repo.update_session(s)
            print(f"Auto-stopped stale session {s.session_id} (started {s.started_at})")
    if status:
        sessions = [s for s in sessions if s.status == status]
    return [
        MonitoringSessionResponse(
            session_id=s.session_id,
            reservation_id=s.reservation_id,
            user_id=s.user_id,
            exam_id=s.exam_id,
            status=s.status,
            started_at=s.started_at,
            stopped_at=s.stopped_at,
            total_frames_processed=s.total_frames_processed,
            anomaly_count=s.anomaly_count
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=MonitoringSessionResponse)
async def start_monitoring(request: StartMonitoringRequest):
    use_case = StartMonitoring(repo, kafka_publisher)
    try:
        session = await use_case.execute(
            request.reservation_id,
            request.user_id,
            request.exam_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MonitoringSessionResponse(
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


@router.post("/sessions/{session_id}/frame", response_model=ProcessFrameResponse)
async def process_frame(session_id: str, request: ProcessFrameRequest):
    try:
        # Browser-only events (no frame data)
        if request.browser_event and (not request.frame_data or request.frame_data.strip() == ''):
            anomalies = await process_frame_use_case.execute_browser_event(
                session_id,
                request.browser_event
            )
        else:
            frame_bytes = base64.b64decode(request.frame_data)
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                raise ValueError("Could not decode frame data")

            anomalies = await process_frame_use_case.execute(
                session_id,
                frame,
                request.frame_number,
                request.browser_event
            )

        if session_id in active_websockets:
            for ws in active_websockets[session_id]:
                await ws.send_json({
                    "type": "anomalies",
                    "data": [
                        {
                            "anomaly_id": a.anomaly_id,
                            "anomaly_type": a.anomaly_type,
                            "severity": a.severity,
                            "description": a.description
                        }
                        for a in anomalies
                    ]
                })

        # Forward frame to live view WebSockets
        if session_id in live_view_websockets:
            live_payload = {
                "type": "frame",
                "frame_data": request.frame_data,
                "frame_number": request.frame_number,
                "timestamp": datetime.utcnow().isoformat(),
                "anomalies": [
                    {
                        "anomaly_id": a.anomaly_id,
                        "anomaly_type": a.anomaly_type,
                        "severity": a.severity,
                        "description": a.description
                    }
                    for a in anomalies
                ]
            }
            dead_connections = []
            for ws in live_view_websockets[session_id]:
                try:
                    await ws.send_json(live_payload)
                except Exception:
                    dead_connections.append(ws)
            for ws in dead_connections:
                live_view_websockets[session_id].remove(ws)
            if not live_view_websockets[session_id]:
                del live_view_websockets[session_id]

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ProcessFrameResponse(
        session_id=session_id,
        frame_number=request.frame_number,
        anomalies_detected=[
            AnomalyResponse(
                anomaly_id=a.anomaly_id,
                session_id=a.session_id,
                anomaly_type=a.anomaly_type,
                severity=a.severity,
                detection_method=a.detection_method,
                confidence=a.confidence,
                detected_at=a.detected_at,
                frame_path=a.frame_path,
                description=a.description,
                metadata=a.metadata
            )
            for a in anomalies
        ]
    )


@router.put("/sessions/{session_id}/stop", response_model=MonitoringSessionResponse)
async def stop_monitoring(session_id: str):
    use_case = StopMonitoring(repo, kafka_publisher)
    try:
        session = await use_case.execute(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Notify live view WebSockets that session is stopped
    if session_id in live_view_websockets:
        for ws in live_view_websockets[session_id]:
            try:
                await ws.send_json({"type": "session_stopped"})
                await ws.close()
            except Exception:
                pass
        del live_view_websockets[session_id]

    return MonitoringSessionResponse(
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


@router.get("/sessions/{session_id}", response_model=MonitoringSessionResponse)
def get_session(session_id: str):
    session = repo.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return MonitoringSessionResponse(
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


@router.get("/sessions/{session_id}/anomalies", response_model=List[AnomalyResponse])
def get_anomalies(session_id: str, severity: Optional[str] = None):
    use_case = GetAnomalies(repo)
    try:
        anomalies = use_case.execute(session_id, severity)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return [
        AnomalyResponse(
            anomaly_id=a.anomaly_id,
            session_id=a.session_id,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            detection_method=a.detection_method,
            confidence=a.confidence,
            detected_at=a.detected_at,
            frame_path=a.frame_path,
            description=a.description,
            metadata=a.metadata
        )
        for a in anomalies
    ]


@router.get("/sessions/{session_id}/anomalies/summary", response_model=AnomalySummaryResponse)
def get_anomaly_summary(session_id: str):
    use_case = GetAnomalySummary(repo)
    try:
        summary = use_case.execute(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return AnomalySummaryResponse(**summary)


@router.get("/frames")
def get_frame_image(path: str):
    """Serve a stored frame image by its storage path."""
    frame = frame_storage.get_frame(path)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    _, encoded = cv2.imencode('.jpg', frame)
    return Response(content=encoded.tobytes(), media_type="image/jpeg")


@router.websocket("/sessions/{session_id}/stream")
async def websocket_stream(websocket: WebSocket, session_id: str):
    await websocket.accept()

    session = repo.get_session_by_id(session_id)
    if not session or session.status != "active":
        await websocket.close(code=4004, reason="Session not found or not active")
        return

    if session_id not in active_websockets:
        active_websockets[session_id] = []
    active_websockets[session_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "frame":
                frame_data = data.get("frame_data")
                frame_number = data.get("frame_number", 0)
                browser_event = data.get("browser_event")

                frame_bytes = base64.b64decode(frame_data)
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is not None:
                    anomalies = await process_frame_use_case.execute(
                        session_id,
                        frame,
                        frame_number,
                        browser_event
                    )

                    await websocket.send_json({
                        "type": "frame_processed",
                        "frame_number": frame_number,
                        "anomalies": [
                            {
                                "anomaly_id": a.anomaly_id,
                                "anomaly_type": a.anomaly_type,
                                "severity": a.severity,
                                "confidence": a.confidence,
                                "description": a.description
                            }
                            for a in anomalies
                        ]
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        if session_id in active_websockets:
            active_websockets[session_id].remove(websocket)
            if not active_websockets[session_id]:
                del active_websockets[session_id]


@router.websocket("/sessions/{session_id}/live")
async def websocket_live_view(websocket: WebSocket, session_id: str):
    await websocket.accept()

    session = repo.get_session_by_id(session_id)
    if not session or session.status != "active":
        await websocket.close(code=4004, reason="Session not found or not active")
        return

    if session_id not in live_view_websockets:
        live_view_websockets[session_id] = []
    live_view_websockets[session_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        if session_id in live_view_websockets:
            if websocket in live_view_websockets[session_id]:
                live_view_websockets[session_id].remove(websocket)
            if not live_view_websockets[session_id]:
                del live_view_websockets[session_id]
