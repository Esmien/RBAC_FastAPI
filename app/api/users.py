from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.user import UserRead, UserUpdate
from app.models.users import User
from app.api.deps import get_current_user, PermissionChecker


router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получение информации о текущем пользователе",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Проверка текущего пользователя

    Args:
        current_user: текущий пользователь
    Returns:
        UserRead: пользователь
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Обновление данных текущего пользователя",
)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Обновление данных текущего пользователя

    Args:
        user_update: данные для обновления
        current_user: текущий пользователь
        session: сессия БД

    Returns:
        UserRead: обновленный профиль пользователя
    """

    # Обновляем данные пользователя
    for key, value in user_update.model_dump(exclude_unset=True).items():
        if value:
            setattr(current_user, key, value)

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="'Мягкое' удаление текущего пользователя",
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    'Мягкое' удаление пользователя

    Args:
        current_user: текущий пользователь
        session: сессия БД
    Returns:
        JSON: сообщение об успешном удалении
    """

    # Удаляем пользователя, делая его неактивным
    current_user.is_active = False
    session.add(current_user)
    await session.commit()
    return {"message": f"Пользователь {current_user.name} удален"}


@router.get(
    "/users",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Получение списка всех пользователей",
)
async def get_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(
        PermissionChecker(business_element="users", permission="read_all_permission")
    ),
):
    """
    Получение списка всех пользователей, доступно только пользователям с разрешением на чтение всего

    Args:
        session: сессия БД
        _: текущий пользователь, проверка прав
    Returns:
        list[UserRead]: список пользователей
    """

    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()
