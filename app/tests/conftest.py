import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.main import app
from app.database.session import Base, get_session
from app.core.config import DATABASE_URL, POSTGRES_DB
from app.database.init_db import init_db


TEST_DATABASE_URL = DATABASE_URL.replace(POSTGRES_DB, "test_db_pytest")

# URL для подключения к системной БД, чтобы создать тестовую
SYSTEM_DATABASE_URL = DATABASE_URL.replace(POSTGRES_DB, "postgres")

# Создание сессии для тестовой БД
engine_test = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
async_session_maker = async_sessionmaker(bind=engine_test, expire_on_commit=False)


# Перекрываем фикстуру get_session
async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


# Фикстуры
@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для сессии тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def create_test_database():
    """
    Создает тестовую базу данных перед запуском всех тестов
    и удаляет её после завершения.
    """
    # Подключаемся к системной базе
    sys_engine = create_async_engine(SYSTEM_DATABASE_URL, poolclass=NullPool)

    async with sys_engine.connect() as conn:
        # Включаем режим autocommit
        await conn.execution_options(isolation_level="AUTOCOMMIT")

        # Сбрасываем активные соединения к тестовой БД (если вдруг зависли)
        await conn.execute(
            text(
                """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'test_db_pytest'
            AND pid <> pg_backend_pid();
            """
            )
        )

        # Пересоздаем базу
        await conn.execute(text("DROP DATABASE IF EXISTS test_db_pytest"))
        await conn.execute(text("CREATE DATABASE test_db_pytest"))

    yield  # Здесь запускаются все тесты

    # Очистка после тестов
    async with sys_engine.connect() as conn:
        await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(
            text(
                """
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'test_db_pytest'
            AND pid <> pg_backend_pid();
            """
            )
        )
        await conn.execute(text("DROP DATABASE IF EXISTS test_db_pytest"))

    await sys_engine.dispose()


@pytest.fixture(scope="function")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный клиент"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="function")
async def session():
    """Сессия БД для тестов"""
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
async def prepare_database(create_test_database):  # Зависим от создания БД
    """
    Создает таблицы перед каждым тестом и дропает после.
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def setup_db(session):
    """Наполняет базу начальными данными (роли, админ)"""
    await init_db(session)
    yield
