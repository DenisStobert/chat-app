# Используем официальный образ Python
FROM python:3.11

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости в контейнер
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install pytest pytest-asyncio httpx

# Копируем все файлы проекта внутрь контейнера
COPY . /app

# Открываем порт 8000
EXPOSE 8000

# Запускаем приложение FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
