import subprocess
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from loguru import logger

from app.api import auth, users, admin, business_elements
from app.database.session import async_session
from app.database.init_db import init_db
from app.core.config import UVI_HOST, UVI_PORT


def run_migrations():
    subprocess.run(["alembic", "upgrade", "head"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()

    async with async_session() as session:
        await init_db(session)
        yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router, prefix="/users", tags=["Пользователи"])
app.include_router(users.router, prefix="/users", tags=["Пользователи"])
app.include_router(admin.router, prefix="/admin", tags=["Админка"])
app.include_router(
    business_elements.router, prefix="/business-elements", tags=["Бизнес-элементы"]
)

if __name__ == "__main__":
    logger.info("Запускаю сервер")
    uvicorn.run(
        "app.main:app",
        host=UVI_HOST,
        port=UVI_PORT,
        reload=True,
    )
