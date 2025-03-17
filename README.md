# FastAPI WebSocket Chat

## Описание проекта
Этот проект представляет собой чат, разработанный с использованием **FastAPI**, **WebSockets** и **PostgreSQL**. Он поддерживает:
- Личные и групповые чаты.
- Обмен текстовыми сообщениями в реальном времени.
- Хранение сообщений в базе данных.
- Отметку о прочтении сообщений.
- JWT-аутентификацию.
- Запуск в **Docker**.

## Технологии
- **Python** (FastAPI, asyncio)
- **PostgreSQL** (асинхронная работа через SQLAlchemy + Asyncpg)
- **WebSockets** (реализация real-time взаимодействия)
- **Docker & Docker Compose** (контейнеризация)
- **JWT (OAuth2)** (авторизация пользователей)
- **Pytest** (юнит-тестирование)

---

## Установка и запуск
### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/chat-app.git
cd chat-app
```

### 2. Создание .env файла
Создайте файл `.env` в корне проекта и укажите переменные:
```env
DATABASE_URL=postgresql+asyncpg://user:password@db/new_chat_db
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Запуск проекта через Docker
```bash
docker-compose up --build
```
> **Примечание:** Подождите 5-10 секунд после старта, пока PostgreSQL полностью инициализируется.

---

## API Документация
После запуска FastAPI автоматически создаст документацию:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Тестирование API
Скачайте и установите **Postman** с официального сайта.


### 1. Регистрация пользователя
1. Открыть **Postman**.
2. Выбрать **POST**..
3. Ввести URL:
```bash
http://localhost:8000/register
```
4. Перейти во вкладку **Body →** выбрать **raw →** выбрать **JSON**.
5. Вставить:
```json
{
    "name": "User1",
    "email": "user1@example.com",
    "password": "password123"
}
```
6. Нажать **Send**.

### 2. Авторизация (получение JWT токена)
1. Выбрать **POST**.
2. Ввести URL:
```bash
http://localhost:8000/token
```
3. Перейти во вкладку **Body →** выбрать **x-www-form-urlencoded**.
4. Добавить параметры:
    - username: user1@example.com
    - password: password123
5. Нажать **Send**.
**Ответ**:
```json
{
    "access_token": "your_jwt_token",
    "token_type": "bearer"
}
```
Скопируйте your_jwt_token, он понадобится для всех следующих запросов.

### 3. Создание чата
1. Выбрать **POST**..
2. Ввести URL:
```bash
http://localhost:8000/chats
```
3. Перейти во вкладку **Headers** и добавить:
 -[] Authorization: Bearer your_jwt_token
4. Перейти во вкладку **Body →** выбрать **raw →** выбрать **JSON**.
5. Вставить:
```json
{
    "name": "Test Chat",
    "chat_type": "group"
}
```
6. Нажать **Send**.

Ответ:
```json
{
    "message": "Чат создан",
    "chat_id": 1
}
```

### 4. Добавление пользователя в чат
1. Выбрать **POST**..
2. Ввести URL:
```bash
http://localhost:8000/chats/1/members?user_id=1
```
3. В **Headers** добавить:
 -[] Authorization: Bearer your_jwt_token
4. Нажать **Send**.
Ответ:
```json
{
    "message": "Пользователь 1 добавлен в чат 1"
}
```

### 5. Получение истории сообщений
1. Выбрать **GET**..
2. Ввести URL:
```bash
http://localhost:8000/history/1
```
3. В **Headers** добавить:
 -[] Authorization: Bearer your_jwt_token
4. Нажать **Send**.
Ответ:
```json
[]
```
Если в чате есть сообщения, вернется список с ними.


---

## WebSocket Подключение
### 1. Подключение к WebSocket
1. В Postman нажать **New →** выбрать **WebSocket Request**.
2. Ввести URL:
```bash
ws://localhost:8000/ws/1/1
```
3. Нажать **Connect**.

### 2. Отправка сообщений
1. В поле отправки ввести JSON:
```json
"Hello, World!"
```
2. Нажать **Send**.
Ответ:
```json
"✅ Сообщение 'Hello, World!' отправлено!"
```

### 3. Получение уведомлений о прочтении
## Обычная отметка о прочтении
При отправке `PUT /message/read/{message_id}` отправитель получит WebSocket-сообщение:
1. Выбрать **PUT**.
2. Ввести URL:
```bash
http://localhost:8000/message/read/1
```
3. В **Headers** добавить:
    -[] Authorization: Bearer your_jwt_token (Токен того, кто прочитал сообщение)
4. Нажать **Send**.
Ответ:
```json
{
    "message": "Сообщение отмечено как прочитанное"
}
```
В WebSocket подключении отправитель получит сообщение "Ваше сообщение 1 прочитано!".

## Ожидание полного прочтения
Если в чате 3 участника, а сообщение отправил 1 пользователь, то оно должно быть прочитано остальными 2.
    -[] Когда 1 пользователь отмечает сообщение прочитанным, WebSocket-уведомление отправителю НЕ отправляется сразу.
    -[]Когда все участники чата (кроме отправителя) отметили сообщение прочитанным, WebSocket-уведомление отправителю отправляется.
Пример работы: 
1. **User1** отправляет сообщение id=10
2. **User2** делает **PUT**-запрос /message/read/10:
    -[] Auth: Bearer Token: user2_token
Ответ:
```json
{
    "message": "Сообщение отмечено как прочитанное"
}
```
WebSocket-уведомления отправителю (User1) пока нет.
3. **User3** делает **PUT**-запрос /message/read/10:
    -[] Auth: Bearer Token: user3_token
Ответ:
```json
{
    "message": "Сообщение 10 полностью прочитано!"
}
```
WebSocket-сообщение отправителю (User1):
```json
"✅ Ваше сообщение 10 полностью прочитано!"
```

---

## Юнит-тестирование
Запустите тесты с `pytest` внутри Docker-контейнера:
```bash
docker-compose exec fastapi_app pytest -v -s --disable-warnings
```

---

## Заключение
Этот проект реализует все ключевые требования:
✔ Подключение пользователей через WebSocket
✔ Обмен текстовыми сообщениями в реальном времени
✔ Создание личных и групповых чатов
✔ Сохранение сообщений в PostgreSQL
✔ Обработка статуса "прочитано"
✔ Предотвращение дублирования сообщений
✔ Контейнеризация (Docker + PostgreSQL)
✔ JWT-аутентификация
✔ Автоматическая документация API
✔ Поддержка нескольких устройств одновременно
✔ Юнит-тестирование с `pytest`

**Для улучшения:** можно добавить поддержку вложений (изображения, файлы) и шифрование сообщений.

## Контакты
**Telegram**: @denisstobert
**Почта**: den.stobert1@gmail.com