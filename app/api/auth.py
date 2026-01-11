from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import sys

from app.api.deps import get_current_user
from app.core.config import LOGGER_CONFIG
from app.database.session import get_session
from app.models.users import User, Role
from app.schemas.user import UserRead, Token, UserRegister, UserRestore
from app.core.security import get_password_hash, create_access_token, check_users_creds


logger.remove()

logger.add(
    sys.stderr,
    **LOGGER_CONFIG,
)


router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=201)
async def register_user(
    user_in: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    """
    Регистрирует пользователя, назначая ему по умолчанию роль "user"

    Args:
        user_in (UserRegister): Пользователь, которого нужно зарегистрировать
        session (AsyncSession): Сессия БД

    Returns:
        UserRead: Зарегистрированный пользователь
    """

    # Проверка на существование пользователя с таким же email
    query = select(User).where(User.email == user_in.email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован!",
        )

    # Назначаем пользователю роль "user"
    query_role = select(Role).where(Role.name == "user")
    result_role = await session.execute(query_role)
    role_obj = result_role.scalar_one_or_none()

    if role_obj is None:
        role_obj = Role(name="user")
        session.add(role_obj)
        await session.commit()
        await session.refresh(role_obj)

    role_id = role_obj.id

    # Создаем нового пользователя, формируем его объект и добавляем в БД
    new_user = User(
        email=str(user_in.email),
        hashed_password=get_password_hash(user_in.password),
        name=user_in.name,
        surname=user_in.surname,
        last_name=user_in.last_name,
        role_id=int(str(role_id)),  # чтобы IDE не ругалась
        is_active=True,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.patch("/restore", response_model=UserRestore, status_code=201)
async def restore_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_session)
):
    """
        Восстанавливает активность пользователя после 'мягкого' удаления

        Args:
            form_data (OAuth2PasswordRequestForm): Данные для восстановления
            session (AsyncSession): Сессия БД

        Raises:
            HTTPException: Если пользователь не найден (404), уже активен (409) или неверный пароль (401)

        Returns:
            UserRestore: Восстановленный пользователь и сообщение об успешном восстановлении
    """

    user = await check_users_creds(form_data.username, form_data.password, session)

    if user.is_active:
        logger.warning(f"Пользователь {user.name} уже активен")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь уже активен"
        )

    user.is_active = True

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info(f"Пользователь {user.name} восстановлен")
    return UserRestore(
        message=f"Пользователь {user.name} успешно восстановлен",
        user=user
    )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """
    Аутентификация пользователя

    Args:
        form_data (OAuth2PasswordRequestForm): Данные для аутентификации
        session (AsyncSession): Сессия БД

    Returns:
        Token: Токен доступа
    """

    user = await check_users_creds(form_data.username, form_data.password, session)

    # Проверяем активность пользователя
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не активен",
        )

    # Создаем токен доступа
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Выход пользователя из системы
    Примечание: мы используем JWT, поэтому здесь ничего не делаем

    Args:
        current_user (User): Текущий пользователь

    Returns:
        Сообщение об успешном выходе
    """

    return {"message": "Вы успешно вышли из системы"}
