from typing import List, Optional

from infrastructure.database.models import NotificationModel, UserPreferenceModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.notification import Notification
from domain.entities.user_preference import UserPreference
from application.interfaces.notification_repository import NotificationRepository


class SQLAlchemyNotificationRepository(NotificationRepository):

    def create_notification(self, notification: Notification) -> None:
        session = SessionLocal()
        db_notification = NotificationModel(
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
            extra_data=notification.metadata
        )
        session.add(db_notification)
        session.commit()
        session.close()

    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        session = SessionLocal()
        result = session.query(NotificationModel).filter_by(notification_id=notification_id).first()
        session.close()
        if not result:
            return None
        return Notification(
            notification_id=result.notification_id,
            user_id=result.user_id,
            notification_type=result.notification_type,
            channel=result.channel,
            subject=result.subject,
            body=result.body,
            status=result.status,
            created_at=result.created_at,
            sent_at=result.sent_at,
            error_message=result.error_message,
            metadata=result.extra_data
        )

    def get_notifications_by_user(self, user_id: str, limit: int = 50) -> List[Notification]:
        session = SessionLocal()
        results = session.query(NotificationModel).filter_by(user_id=user_id).order_by(
            NotificationModel.created_at.desc()
        ).limit(limit).all()
        session.close()
        return [
            Notification(
                notification_id=r.notification_id,
                user_id=r.user_id,
                notification_type=r.notification_type,
                channel=r.channel,
                subject=r.subject,
                body=r.body,
                status=r.status,
                created_at=r.created_at,
                sent_at=r.sent_at,
                error_message=r.error_message,
                metadata=r.extra_data
            )
            for r in results
        ]

    def get_pending_notifications(self) -> List[Notification]:
        session = SessionLocal()
        results = session.query(NotificationModel).filter_by(status="pending").all()
        session.close()
        return [
            Notification(
                notification_id=r.notification_id,
                user_id=r.user_id,
                notification_type=r.notification_type,
                channel=r.channel,
                subject=r.subject,
                body=r.body,
                status=r.status,
                created_at=r.created_at,
                sent_at=r.sent_at,
                error_message=r.error_message,
                metadata=r.extra_data
            )
            for r in results
        ]

    def update_notification(self, notification: Notification) -> None:
        session = SessionLocal()
        db_notification = session.query(NotificationModel).filter_by(
            notification_id=notification.notification_id
        ).first()
        if db_notification:
            db_notification.status = notification.status
            db_notification.sent_at = notification.sent_at
            db_notification.error_message = notification.error_message
            session.commit()
        session.close()

    def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        session = SessionLocal()
        result = session.query(UserPreferenceModel).filter_by(user_id=user_id).first()
        session.close()
        if not result:
            return None
        return UserPreference(
            user_id=result.user_id,
            email=result.email,
            email_enabled=result.email_enabled,
            push_enabled=result.push_enabled,
            push_token=result.push_token,
            notification_types=result.notification_types or [],
            reminder_hours_before=result.reminder_hours_before or [24, 1]
        )

    def save_user_preference(self, preference: UserPreference) -> None:
        session = SessionLocal()
        existing = session.query(UserPreferenceModel).filter_by(user_id=preference.user_id).first()

        if existing:
            existing.email = preference.email
            existing.email_enabled = preference.email_enabled
            existing.push_enabled = preference.push_enabled
            existing.push_token = preference.push_token
            existing.notification_types = preference.notification_types
            existing.reminder_hours_before = preference.reminder_hours_before
        else:
            db_pref = UserPreferenceModel(
                user_id=preference.user_id,
                email=preference.email,
                email_enabled=preference.email_enabled,
                push_enabled=preference.push_enabled,
                push_token=preference.push_token,
                notification_types=preference.notification_types,
                reminder_hours_before=preference.reminder_hours_before
            )
            session.add(db_pref)

        session.commit()
        session.close()
