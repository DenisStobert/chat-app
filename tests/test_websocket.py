import pytest
import asyncio
import websockets

@pytest.mark.asyncio
async def test_websocket_connection(get_token, setup_chat):
    """Тест WebSocket подключения и отправки сообщений"""

    chat_id = setup_chat  # Чат создан через фикстуру
    uri = f"ws://localhost:8000/ws/1/{chat_id}"  # Подставляем ID чата
    headers = {"Authorization": get_token}  # WebSocket заголовки

    async with websockets.connect(uri, additional_headers=headers) as websocket:
        test_message = "Test WebSocket Message"
        await websocket.send(test_message)

        response = await websocket.recv()

        assert "✅" in response, f"Ошибка: сервер не подтвердил сообщение. Ответ: {response}"
