from sqlalchemy import UniqueConstraint, Table, Column, Integer, String, ForeignKey, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.db import Base

# Таблица для отслеживания прочитанных сообщений
message_readers = Table(
    "message_readers",
    Base.metadata,
    Column("message_id", Integer, ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("message_id", "user_id", name="unique_message_read")
)

# Ассоциативная таблица для связи пользователей и чатов
chat_members = Table(
    "chat_members",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role", String, default="member")  # ✅ Добавляем поддержку ролей
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    chats = relationship("Chat", secondary=chat_members, back_populates="members", passive_deletes=True)

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=True)
    chat_type = Column(String, nullable=False)  # "private" или "group"

    members = relationship("User", secondary=chat_members, back_populates="chats")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    read = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("chat_id", "sender_id", "text", "timestamp", name="unique_message"),
    )