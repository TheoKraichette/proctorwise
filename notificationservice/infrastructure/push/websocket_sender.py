import json
from typing import Dict, Any, Optional
from fastapi import WebSocket

from application.interfaces.push_sender import RealtimeSender


class WebSocketManager:
    """Gestionnaire centralisé des connexions WebSocket."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str) -> None:
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    def is_connected(self, user_id: str) -> bool:
        return user_id in self.active_connections

    async def send_to_user(self, user_id: str, message: dict) -> bool:
        if user_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            print(f"Failed to send WebSocket message to {user_id}: {e}")
            await self.disconnect(user_id)
            return False

    async def broadcast(self, message: dict) -> None:
        disconnected = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(user_id)

        for user_id in disconnected:
            await self.disconnect(user_id)


# Instance globale du gestionnaire WebSocket
ws_manager = WebSocketManager()


class WebSocketSender(RealtimeSender):
    """Implémentation de l'envoi de notifications via WebSocket."""

    def __init__(self, manager: WebSocketManager = None):
        self.manager = manager or ws_manager

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await self.manager.connect(user_id, websocket)

    async def disconnect(self, user_id: str) -> None:
        await self.manager.disconnect(user_id)

    async def send(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        message = {
            "type": "notification",
            "title": title,
            "body": body,
            "data": data or {}
        }
        return await self.manager.send_to_user(user_id, message)

    def is_connected(self, user_id: str) -> bool:
        return self.manager.is_connected(user_id)


class MockRealtimeSender(RealtimeSender):
    """Mock pour les tests sans WebSocket réel."""

    def __init__(self):
        self.sent_notifications = []
        self.connected_users = set()

    async def connect(self, user_id: str, websocket) -> None:
        self.connected_users.add(user_id)

    async def disconnect(self, user_id: str) -> None:
        self.connected_users.discard(user_id)

    async def send(
        self,
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        self.sent_notifications.append({
            "user_id": user_id,
            "title": title,
            "body": body,
            "data": data
        })
        print(f"[MOCK WS] User: {user_id}, Title: {title}")
        return True

    def is_connected(self, user_id: str) -> bool:
        return user_id in self.connected_users
