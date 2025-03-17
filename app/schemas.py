from pydantic import BaseModel
from datetime import datetime

# ✅ Модель для создания пользователя
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

# ✅ Модель для создания сообщений
class MessageCreate(BaseModel):
    chat_id: int
    sender_id: int
    text: str

# ✅ Модель ответа для сообщений
class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    timestamp: datetime
    read: bool

    class Config:
        from_attributes = True

# ✅ Модель для создания чата
class ChatCreate(BaseModel):
    name: str
    chat_type: str  # "private" или "group"
