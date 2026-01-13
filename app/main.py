import subprocess
import sys
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from loguru import logger

from app.api import auth, users, admin, business_elements
from app.database.session import async_session
from app.database.init_db import init_db
from app.core.config import settings


# --- Настройка логгера ---
def setup_logging():
    # Удаляем стандартный обработчик, чтобы не дублировалось
    logger.remove()

    # Добавляем наш настроенный обработчик
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        colorize=settings.LOG_COLORIZE,
    )


def run_migrations():
    subprocess.run(["alembic", "upgrade", "head"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Настраиваем логи при старте
    setup_logging()
    logger.info("🚀 Logger сконфигурирован!")
    logger.info(f"Проверка подключения к БД: {settings.DATABASE_URL.split('@')[-1]}")

    run_migrations()

    async with async_session() as session:
        await init_db(session)
        yield

    logger.info("🛑 Сервис остановлен")


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/users", tags=["Пользователи"])
app.include_router(users.router, prefix="/users", tags=["Пользователи"])
app.include_router(admin.router, prefix="/admin", tags=["Админка"])
app.include_router(business_elements.router, prefix="/business-elements", tags=["Бизнес-элементы"])

if __name__ == "__main__":
    logger.info("Запускаю сервер")
    uvicorn.run(
        "app.main:app",
        host=settings.UVI_HOST,
        port=settings.UVI_PORT,
        reload=True,
    )
