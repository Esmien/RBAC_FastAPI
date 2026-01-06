from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv


class Base(DeclarativeBase):
    pass


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)



async def get_session():
    async with async_session() as session:
        yield session