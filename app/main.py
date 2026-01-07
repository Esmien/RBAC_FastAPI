import subprocess
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from app.api import auth, users
from app.database.db.session import async_session
from app.database.init_db import init_db


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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )