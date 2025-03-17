from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func, text  # Добавлен `text` для SQL-запросов
from sqlalchemy.future import select
from sqlalchemy import insert
from app.models import User, Chat, Message, chat_members, message_readers
from app.schemas import UserCreate, MessageCreate, ChatCreate
from app.websocket import manager

# ✅ Создание нового пользователя
async def create_user(db: AsyncSession, user: UserCreate):
    new_user = User(
        name=user.name,
        email=user.email,
        password=user.password
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        return None

# 🔎 Получение пользователя по email
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_message(db: AsyncSession, chat_id: int, sender_id: int, text: str):
    """Создание нового сообщения с защитой от дубликатов"""
    existing_message = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id, Message.sender_id == sender_id, Message.text == text)
    )
    if existing_message.scalars().first():
        return {"error": "⚠️ Сообщение уже отправлено"}

    new_message = Message(chat_id=chat_id, sender_id=sender_id, text=text, read=False)
    db.add(new_message)
    try:
        await db.commit()
        await db.refresh(new_message)
        return new_message
    except IntegrityError:
        await db.rollback()
        return {"error": "⚠️ Сообщение уже существует"}

# ✅ Создание нового чата
async def create_chat(db: AsyncSession, chat: ChatCreate):
    new_chat = Chat(name=chat.name, chat_type=chat.chat_type)
    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)
    return new_chat

# ✅ Добавление пользователя в чат
async def add_chat_member(db: AsyncSession, chat_id: int, user_id: int):
    chat = await db.get(Chat, chat_id)
    user = await db.get(User, user_id)

    if not chat:
        return {"error": "Чат не найден"}
    if not user:
        return {"error": "Пользователь не найден"}

    # Проверяем, не добавлен ли пользователь уже в чат
    result = await db.execute(
        select(chat_members).where(
            (chat_members.c.chat_id == chat_id) & (chat_members.c.user_id == user_id)
        )
    )
    if result.fetchone():
        return {"message": "⚠️ Пользователь уже в этом чате"}

    # ✅ Добавляем пользователя в чат
    stmt = insert(chat_members).values(chat_id=chat_id, user_id=user_id)
    await db.execute(stmt)
    await db.commit()

    return {"message": f"✅ Пользователь {user_id} добавлен в чат {chat_id}"}

# ✅ Получение списка участников чата
async def get_chat_members(db: AsyncSession, chat_id: int):
    result = await db.execute(
        select(User.id, User.name)
        .join(chat_members, User.id == chat_members.c.user_id)
        .where(chat_members.c.chat_id == chat_id)
    )
    members = result.fetchall()
    return {"chat_id": chat_id, "members": [{"id": user.id, "name": user.name} for user in members]}

# ✅ Получение истории сообщений
async def get_messages(db: AsyncSession, chat_id: int, limit: int = 10, offset: int = 0):
    result = await db.execute(
        select(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp)
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


# ✅ Отметка сообщения как прочитанного
async def mark_message_as_read(db: AsyncSession, message_id: int, user_email: str):
    """Отмечает сообщение как прочитанное пользователем"""

    # 1️⃣ Проверяем, существует ли сообщение
    message = await db.execute(
        text("SELECT sender_id, chat_id FROM messages WHERE id = :message_id"),
        {"message_id": message_id}
    )
    message_data = message.fetchone()

    if not message_data:
        return {"error": "Сообщение не найдено"}
    
    sender_id, chat_id = message_data  # Отправитель и чат ID

    # 2️⃣ Получаем user_id по email
    user = await db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_email})
    user_id = user.scalar()

    if not user_id:
        return {"error": "Пользователь не найден"}

    # 3️⃣ Проверяем, не было ли уже прочитано этим пользователем
    already_read = await db.execute(
        text("SELECT 1 FROM message_readers WHERE message_id = :message_id AND user_id = :user_id"),
        {"message_id": message_id, "user_id": user_id}
    )

    if already_read.fetchone():
        return {"message": f"Сообщение {message_id} уже прочитано пользователем {user_id}"}

    # 4️⃣ Отмечаем сообщение как прочитанное этим пользователем
    await db.execute(
        text("""
            INSERT INTO message_readers (message_id, user_id)
            VALUES (:message_id, :user_id)
            ON CONFLICT DO NOTHING
        """),
        {"message_id": message_id, "user_id": user_id}
    )
    await db.commit()

    # 5️⃣ Проверяем количество участников чата (кроме отправителя)
    total_members = await db.execute(
        text("SELECT COUNT(*) FROM chat_members WHERE chat_id = :chat_id AND user_id != :sender_id"),
        {"chat_id": chat_id, "sender_id": sender_id}
    )
    total_members = total_members.scalar()  # Убираем отправителя из подсчета

    # 6️⃣ Проверяем, сколько уже прочитали
    read_count = await db.execute(
        text("SELECT COUNT(*) FROM message_readers WHERE message_id = :message_id"),
        {"message_id": message_id}
    )
    read_count = read_count.scalar()

    # Логирование
    print(f"📊 Всего участников (без отправителя): {total_members}, Прочитали: {read_count}")

    # 7️⃣ Если **все, кроме отправителя** прочли → Отмечаем "полностью прочитано"
    if read_count == total_members:
        await db.execute(
            text("UPDATE messages SET read = TRUE WHERE id = :message_id"),
            {"message_id": message_id}
        )
        await db.commit()

        print(f"✅ Сообщение {message_id} полностью прочитано!")
        return {"message": f"Сообщение {message_id} полностью прочитано!"}

    return {"message": f"Пользователь {user_id} отметил сообщение {message_id} как прочитанное"}