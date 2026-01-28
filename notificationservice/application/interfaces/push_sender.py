from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class RealtimeSender(ABC):
    """Interface for real-time notification delivery via WebSocket."""

    @abstractmethod
    async def connect(self, user_id: str, websocket) -> None:
        """Register a WebSocket connection for a user."""
        pass

    @abstractmethod
    async def disconnect(self, user_id: str) -> None:
        """Remove a user's WebSocket connection."""
        pass

    @abstractmethod
    async def send(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a real-time notification to a user via WebSocket."""
        pass

    @abstractmethod
    def is_connected(self, user_id: str) -> bool:
        """Check if a user has an active WebSocket connection."""
        pass
