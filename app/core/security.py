import sys

import bcrypt
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from jose import jwt
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    LOGGER_CONFIG,
)
from app.database.session import get_session
from app.models.users import User


logger.remove()

logger.add(
    sys.stderr,
    **LOGGER_CONFIG,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, совпадает ли пароль с хешем

    Args:
        plain_password (str): Пароль в открытом виде
        hashed_password (str): Хеш пароля

    Returns:
        bool: True, если пароль совпадает с хешем, иначе False
    """

    # Превращаем пароль в набор байтов
    password_bytes = plain_password.encode("utf-8")

    # Проверяем, совпадает ли пароль с хешем
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля

    Args:
        password (str): Пароль в открытом виде

    Returns:
        str: Хеш пароля
    """

    # Превращаем пароль в набор байтов
    password_bytes = password.encode("utf-8")

    # Генерируем соль
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    # Возвращаем хеш в виде строки
    return hashed_password.decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Создает JWT токен.

    Args:
        data (dict): Данные, которые мы хотим зашить в токен (например, {"sub": "user_email"}).
        expires_delta (timedelta): Время жизни токена. Если не передано, берем дефолтное.

    Returns:
        str: Закодированный токен.
    """

    # Спасаем исходный словарь от мутаций
    curr_data = data.copy()
    expires_time = datetime.now(timezone.utc)

    # Если время жизни токена не задано, берем дефолтное
    if expires_delta:
        expires_time += expires_delta
    else:
        expires_time += timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    logger.debug(f"Время жизни токена: {expires_time}")

    # Добавляем время жизни токена в словарь
    curr_data["exp"] = expires_time

    return jwt.encode(curr_data, SECRET_KEY, algorithm=ALGORITHM)


async def check_users_creds(
        email: str,
        password: str,
        session: AsyncSession
) -> User:
    """
        Проверка учетных данных пользователя.
        Используется при аутентификации и восстановлении пользователя

        Args:
            email (str): Электронная почта пользователя
            password (str): Пароль пользователя
            session (AsyncSession): Сессия SQLAlchemy для выполнения запросов к базе данных

        Raises:
            HTTPException: Если учетные данные неверны, выбрасывается ошибка 401.

        Returns:
            User: Объект пользователя, если учетные данные верны.
    """
    # Проверяем совпадение пароля и наличие пользователя в БД
    query = select(User).where(User.email == email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    # Если пользователь не найден или пароль не совпадает, выбрасываем 401 ошибку
    if user is None or not verify_password(password, user.hashed_password):
        logger.error(f"Неверный логин или пароль: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
        )

    return user