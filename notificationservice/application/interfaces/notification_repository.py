from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.notification import Notification
from domain.entities.user_preference import UserPreference


class NotificationRepository(ABC):
    @abstractmethod
    def create_notification(self, notification: Notification) -> None:
        pass

    @abstractmethod
    def get_notification_by_id(self, notification_id: str) -> Optional[Notification]:
        pass

    @abstractmethod
    def get_notifications_by_user(self, user_id: str, limit: int = 50) -> List[Notification]:
        pass

    @abstractmethod
    def get_pending_notifications(self) -> List[Notification]:
        pass

    @abstractmethod
    def update_notification(self, notification: Notification) -> None:
        pass

    @abstractmethod
    def get_user_preference(self, user_id: str) -> Optional[UserPreference]:
        pass

    @abstractmethod
    def save_user_preference(self, preference: UserPreference) -> None:
        pass
