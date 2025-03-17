import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_chat(client: AsyncClient, token: str):
    response = await client.post(
        "/chats",
        json={"name": "Test Chat", "chat_type": "group"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "chat_id" in response.json()

@pytest.mark.asyncio
async def test_add_user_to_chat(client: AsyncClient, token: str):
    """Тест добавления пользователя в чат"""

    # 1. Создаём чат
    chat_response = await client.post(
        "/chats",
        json={"name": "Test Chat", "chat_type": "group"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert chat_response.status_code == 200, f"Ошибка создания чата: {chat_response.text}"

    chat_id = chat_response.json().get("chat_id")
    assert chat_id is not None, "chat_id должен быть получен"

    # 2. Пробуем добавить пользователя в чат (user_id в query params!)
    add_user_response = await client.post(
        f"/chats/{chat_id}/members",
        params={"user_id": 1, "role": "member"},  # <-- передаём как params, а не json
        headers={"Authorization": f"Bearer {token}"}
    )

    # Если тест провалится, выведет полный ответ сервера
    assert add_user_response.status_code == 200, f"Ошибка добавления в чат: {add_user_response.text}"
    
@pytest.mark.asyncio
async def test_get_chat_history(client: AsyncClient, token):
    chat_response = await client.post(
        "/chats",
        json={"name": "Test Chat", "chat_type": "group"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert chat_response.status_code == 200
    chat_id = chat_response.json().get("chat_id")
    assert chat_id is not None  

    response = await client.get(
        f"/history/{chat_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
