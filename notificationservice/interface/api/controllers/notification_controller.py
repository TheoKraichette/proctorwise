import os
from typing import List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from application.use_cases.send_notification import SendNotification, GetUserNotifications
from domain.entities.user_preference import UserPreference
from infrastructure.repositories.sqlalchemy_notification_repository import SQLAlchemyNotificationRepository
from infrastructure.email.smtp_email_sender import SMTPEmailSender, MockEmailSender
from infrastructure.push.websocket_sender import WebSocketSender, MockRealtimeSender, ws_manager
from interface.api.schemas.notification_request import SendNotificationRequest, UpdatePreferenceRequest
from interface.api.schemas.notification_response import NotificationResponse, UserPreferenceResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

repo = SQLAlchemyNotificationRepository()

if os.getenv("USE_MOCK_SENDERS", "true").lower() == "true":
    email_sender = MockEmailSender()
    realtime_sender = MockRealtimeSender()
else:
    email_sender = SMTPEmailSender()
    realtime_sender = WebSocketSender()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time notifications."""
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Client can send ping/pong or other messages
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id)


@router.post("/", response_model=NotificationResponse)
async def send_notification(request: SendNotificationRequest):
    use_case = SendNotification(repo, email_sender, realtime_sender)

    notification = await use_case.execute(
        user_id=request.user_id,
        notification_type=request.notification_type,
        subject=request.subject,
        body=request.body,
        channel=request.channel,
        metadata=request.metadata
    )

    if not notification:
        raise HTTPException(status_code=400, detail="Notification not sent - user preferences may have blocked it")

    return NotificationResponse(
        notification_id=notification.notification_id,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        channel=notification.channel,
        subject=notification.subject,
        body=notification.body,
        status=notification.status,
        created_at=notification.created_at,
        sent_at=notification.sent_at,
        error_message=notification.error_message,
        metadata=notification.metadata
    )


@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(user_id: str, limit: int = 50):
    use_case = GetUserNotifications(repo)
    notifications = use_case.execute(user_id, limit)

    return [
        NotificationResponse(
            notification_id=n.notification_id,
            user_id=n.user_id,
            notification_type=n.notification_type,
            channel=n.channel,
            subject=n.subject,
            body=n.body,
            status=n.status,
            created_at=n.created_at,
            sent_at=n.sent_at,
            error_message=n.error_message,
            metadata=n.metadata
        )
        for n in notifications
    ]


@router.get("/preferences/{user_id}", response_model=UserPreferenceResponse)
def get_user_preferences(user_id: str):
    preference = repo.get_user_preference(user_id)

    if not preference:
        raise HTTPException(status_code=404, detail=f"Preferences not found for user {user_id}")

    return UserPreferenceResponse(
        user_id=preference.user_id,
        email_enabled=preference.email_enabled,
        websocket_enabled=preference.websocket_enabled,
        notification_types=preference.notification_types
    )


@router.put("/preferences/{user_id}", response_model=UserPreferenceResponse)
def update_user_preferences(user_id: str, request: UpdatePreferenceRequest):
    preference = UserPreference(
        user_id=user_id,
        email_enabled=request.email_enabled,
        websocket_enabled=request.websocket_enabled,
        notification_types=request.notification_types
    )

    repo.save_user_preference(preference)

    return UserPreferenceResponse(
        user_id=preference.user_id,
        email_enabled=preference.email_enabled,
        websocket_enabled=preference.websocket_enabled,
        notification_types=preference.notification_types
    )
