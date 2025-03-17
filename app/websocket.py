from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # Поддержка нескольких устройств

    async def connect(self, websocket: WebSocket, user_id: int):
        """Добавляем WebSocket соединение для пользователя"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        """Отключаем WebSocket соединение для пользователя"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:  # Если список пуст, удаляем user_id
                del self.active_connections[user_id]

    async def send_message(self, user_id: int, message: str):
        """Отправляем сообщение на все устройства пользователя"""
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message)
                except WebSocketDisconnect:
                    self.disconnect(user_id, websocket)

    async def mark_as_read(self, user_id: int, message_id: int):
        """Уведомляем пользователя о прочитанном сообщении"""
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(f"✅ Ваше сообщение {message_id} прочитано!")
                except WebSocketDisconnect:
                    self.disconnect(user_id, websocket)

manager = ConnectionManager()
