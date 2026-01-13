from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_session
from app.models.users import User
from app.models.rbac import AccessRule, BusinessElement
from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Возвращает текущего пользователя

    Args:
        token: токен пользователя
        session: сессия базы данных
    Returns:
        User: пользователь
    Raises:
        HTTPException: если токен не валиден
    """

    # Создание исключения для невалидного токена
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка валидации токена",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Декодирование токена
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub", None)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Поиск пользователя по id
    query = select(User).where(User.id == int(user_id))
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    # Проверка наличия пользователя и его активности
    if user is None or not user.is_active:
        raise credentials_exception
    else:
        return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Проверяет, является ли пользователь админом

    Args:
        current_user: текущий пользователь

    Raises:
        HTTPException: если пользователь не админ

    Returns:
        User: текущий пользователь с правами админа
    """

    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для выполнения этого действия необходимы права администратора",
        )

    return current_user


async def get_user_by_id(user_id: int, session: AsyncSession) -> User:
    """
    Возвращает пользователя по id

    Args:
        user_id: id пользователя
        session: сессия базы данных

    Raises:
        HTTPException: если пользователь не найден (404)

    Returns:
        User: пользователь
    """

    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с id {user_id} не найден",
        )

    return user


class PermissionChecker:
    """
    Проверяет наличие прав у пользователя

    Attributes:
        business_element: элемент бизнес-логики
        permission: право доступа
    """

    def __init__(self, business_element: str, permission: str):
        self.business_element = business_element
        self.permission = permission

    async def __call__(
        self,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """
        Проверяет наличие прав у пользователя

        Args:
            user: текущий пользователь
            session: сессия базы данных

        Raises:
            HTTPException: если у пользователя нет прав или нет искомого элемента(403)
        """

        # Поиск элемента бизнес-логики и прав доступа
        query = (
            select(AccessRule)
            .join(BusinessElement)
            .where(
                AccessRule.role_id == user.role_id,
                BusinessElement.name == self.business_element,
            )
        )
        result = await session.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Права доступа не найдены",
            )

        # Проверка наличия прав у пользователя
        permission_value = getattr(rule, self.permission)

        if not permission_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на выполнение этого действия",
            )

        return user
