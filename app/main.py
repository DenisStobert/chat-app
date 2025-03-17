from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router  # Наши REST и WebSocket маршруты
from app.db import Base, engine

app = FastAPI()

# Разрешаем CORS и WebSocket с любых источников
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все домены (при необходимости можно указать конкретные)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация всех маршрутов из router
app.include_router(router)

# Автоматическое создание таблиц в базе данных при старте
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("✅ База данных инициализирована")
