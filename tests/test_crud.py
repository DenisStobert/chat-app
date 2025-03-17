from app.models import User
from app.schemas import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_password_hash

async def create_user(db: AsyncSession, user: UserCreate):
    """Создание пользователя в БД"""
    new_user = User(
        name=user.name,
        email=user.email,
        password=get_password_hash(user.password),
    )
    db.add(new_user)
    await db.flush()  # ✅ Используем flush() вместо commit()
    await db.refresh(new_user)
    return new_user
