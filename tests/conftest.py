import os
import uuid
import pytest
import pytest_asyncio
import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.sql import text
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db import get_db
from app.schemas import UserCreate
from app.auth import create_access_token
from app.crud import create_user
from dotenv import load_dotenv

# Загружаем тестовые переменные окружения
load_dotenv(".env.test")

# Подключение к тестовой базе данных
DATABASE_URL = os.getenv("DATABASE_URL")

# Создаем движок и фабрику сессий
engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="function")
async def get_token():
    """Фикстура для получения токена пользователя"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Регистрируем пользователя
        await client.post(
            "/register",
            json={"name": "Test User", "email": "test@example.com", "password": "password123"},
        )

        # Получаем JWT токен
        response = await client.post(
            "/token",
            data={"username": "test@example.com", "password": "password123"},
        )

        return f"Bearer {response.json()['access_token']}"

@pytest.fixture(scope="function")
async def setup_chat(get_token):
    """Фикстура для создания чата и добавления пользователя"""
    headers = {"Authorization": get_token}

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Создаем чат
        chat_response = await client.post(
            "/chats",
            json={"name": "Test Chat", "chat_type": "group"},
            headers=headers
        )
        chat_id = chat_response.json()["chat_id"]

        # Добавляем пользователя в чат (user_id=1)
        await client.post(
            f"/chats/{chat_id}/members?user_id=1",
            headers=headers
        )

        return chat_id

# Глобальный event loop для всех тестов
@pytest.fixture(scope="session")
def event_loop():
    """Гарантирует, что все тесты используют один и тот же event loop."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def session():
    """Создает сессию для каждого теста"""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()

@pytest_asyncio.fixture(scope="function")
async def token(session: AsyncSession):
    """Создание тестового пользователя и JWT-токена"""
    test_user = UserCreate(
        name="Test User",
        email=f"test_{uuid.uuid4()}@example.com",
        password="testpassword"
    )
    user = await create_user(session, test_user)
    await session.commit()
    return create_access_token({"sub": user.email})

@pytest_asyncio.fixture(scope="function")
async def client(session: AsyncSession):
    """Создаёт HTTP-клиент и использует тестовую БД"""
    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

    # Очистка базы данных после каждого теста
    async with TestingSessionLocal() as cleanup_session:
        await cleanup_session.execute(text("DELETE FROM chat_members"))  # Удаляем связи пользователей с чатами
        await cleanup_session.execute(text("DELETE FROM users"))  # Теперь можно удалить пользователей
        await cleanup_session.execute(text("DELETE FROM chats"))  # Удаляем чаты
        await cleanup_session.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
        await cleanup_session.execute(text("ALTER SEQUENCE chats_id_seq RESTART WITH 1"))
        await cleanup_session.commit()
        await cleanup_session.close()

