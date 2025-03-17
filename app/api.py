from fastapi import Header, status, APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
import ast
from sqlalchemy.sql import text

from app.auth import SECRET_KEY, ALGORITHM, verify_password, create_access_token, get_password_hash
from app.db import get_db, SessionLocal
from app.crud import mark_message_as_read, get_messages, create_chat, add_chat_member, get_chat_members, create_message, create_user, get_user_by_email
from app.websocket import manager
from app.schemas import MessageCreate, UserCreate, ChatCreate
from app.models import Message, User, Chat

router = APIRouter()

### 🚀 **WebSocket подключение**
@router.websocket("/ws/{user_id}/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, chat_id: int):
    """Подключение пользователя через WebSocket и обработка сообщений в реальном времени."""
    print(f"👤 Пользователь {user_id} подключается к чату {chat_id}")
    
    async with SessionLocal() as db:
        members = await get_chat_members(db, chat_id)
        if not any(member["id"] == user_id for member in members["members"]):
            await websocket.close(code=1008)  # Код 1008 - policy violation
            print(f"❌ Пользователь {user_id} НЕ состоит в чате {chat_id}. Закрываем WebSocket.")
            return

    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Получено сообщение от {user_id}: {data}")

            async with SessionLocal() as db:
                new_message = await create_message(db, chat_id, user_id, data)

                if isinstance(new_message, dict) and "error" in new_message:
                    await manager.send_message(user_id, new_message["error"])
                    continue  # Если сообщение дубликат - пропускаем отправку

                members = await get_chat_members(db, chat_id)
                for member in members["members"]:
                    if member["id"] != user_id:
                        await manager.send_message(member["id"], f"📩 Новое сообщение от {user_id}: {data}")

                await manager.send_message(user_id, f"✅ Сообщение '{data}' отправлено!")

    except WebSocketDisconnect:
        print(f"❌ Пользователь {user_id} отключился")
        manager.disconnect(user_id, websocket)

### 📜 **История сообщений**
@router.get("/history/{chat_id}")
async def get_chat_history(chat_id: int, db: AsyncSession = Depends(get_db)):
    return await get_messages(db, chat_id)

### ✅ **Отметка о прочтении сообщений**
@router.put("/message/read/{message_id}")
async def mark_message_read(
    message_id: int, 
    db: AsyncSession = Depends(get_db),
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    try:
        token = authorization.split(" ")[1]  # Убираем "Bearer"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # ✅ Теперь `sub` — это email пользователя
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token structure")

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Отмечаем сообщение прочитанным
    result = await mark_message_as_read(db, message_id, user_email)  

    if "error" not in result:
        async with SessionLocal() as db:
            message = await db.get(Message, message_id)
            
            if message:
                # 1️⃣ Проверяем, сколько людей должны прочитать (без отправителя)
                total_members = await db.execute(
                    text("SELECT COUNT(*) FROM chat_members WHERE chat_id = :chat_id AND user_id != :sender_id"),
                    {"chat_id": message.chat_id, "sender_id": message.sender_id}
                )
                total_members = total_members.scalar()

                # 2️⃣ Проверяем, сколько уже прочитали
                read_count = await db.execute(
                    text("SELECT COUNT(*) FROM message_readers WHERE message_id = :message_id"),
                    {"message_id": message_id}
                )
                read_count = read_count.scalar()

                # 3️⃣ Если это **последний пользователь**, отправляем уведомление
                if read_count == total_members:
                    await manager.send_message(message.sender_id, f"✅ Ваше сообщение {message_id} прочитано!")

    return result

### 🔹 **Создание чата**
@router.post("/chats")
async def create_new_chat(chat: ChatCreate, db: AsyncSession = Depends(get_db)):
    new_chat = await create_chat(db, chat)
    return {"message": "✅ Чат создан", "chat_id": new_chat.id}

### 👥 **Добавление пользователей в чат**
@router.post("/chats/{chat_id}/members")
async def add_user_to_chat(chat_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    return await add_chat_member(db, chat_id, user_id)

### 🔍 **Просмотр участников чата**
@router.get("/chats/{chat_id}/members")
async def get_chat_users(chat_id: int, db: AsyncSession = Depends(get_db)):
    return await get_chat_members(db, chat_id)

# 🔐 **Регистрация пользователя**
@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user.password = get_password_hash(user.password)
    new_user = await create_user(db, user)
    return {"message": "Пользователь успешно зарегистрирован!"}

# 🔑 **Получение токена (авторизация пользователя)**
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Неправильная почта или пароль")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
