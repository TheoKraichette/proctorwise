from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from domain.entities.notification import Notification
from application.interfaces.notification_repository import NotificationRepository
from application.interfaces.email_sender import EmailSender
from application.interfaces.push_sender import RealtimeSender


class SendNotification:
    def __init__(
        self,
        repository: NotificationRepository,
        email_sender: EmailSender,
        push_sender: RealtimeSender
    ):
        self.repository = repository
        self.email_sender = email_sender
        self.push_sender = push_sender

    async def execute(
        self,
        user_id: str,
        notification_type: str,
        subject: str,
        body: str,
        channel: str = "both",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        preference = self.repository.get_user_preference(user_id)

        if preference and notification_type not in preference.notification_types:
            return None

        notification = Notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            subject=subject,
            body=body,
            status="pending",
            created_at=datetime.utcnow(),
            metadata=metadata
        )

        self.repository.create_notification(notification)

        success = False
        errors = []

        if channel in ["email", "both"] and preference and preference.email_enabled:
            try:
                email_success = await self.email_sender.send(
                    preference.email,
                    subject,
                    body
                )
                if email_success:
                    success = True
                else:
                    errors.append("Email delivery failed")
            except Exception as e:
                errors.append(f"Email error: {str(e)}")

        if channel in ["push", "both"] and preference and preference.push_enabled:
            try:
                push_success = await self.push_sender.send(
                    user_id,
                    subject,
                    body,
                    metadata
                )
                if push_success:
                    success = True
                else:
                    errors.append("Push notification failed")
            except Exception as e:
                errors.append(f"Push error: {str(e)}")

        notification.status = "sent" if success else "failed"
        notification.sent_at = datetime.utcnow() if success else None
        notification.error_message = "; ".join(errors) if errors else None

        self.repository.update_notification(notification)

        return notification


class GetUserNotifications:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def execute(self, user_id: str, limit: int = 50):
        return self.repository.get_notifications_by_user(user_id, limit)
