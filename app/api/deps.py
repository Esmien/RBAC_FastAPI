from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.db.session import get_session
from app.models.users import User
from app.models.rbac import AccessRule, BusinessElement
from app.core.config import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session)
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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


class PermissionChecker:
    def __init__(self, business_element: str, permission: str):
        self.business_element = business_element
        self.permission = permission

    async def __call__(
            self,
            user: User = Depends(get_current_user),
            session: AsyncSession = Depends(get_session)
    ) -> User:
        """
            Проверяет наличие прав у пользователя

            Args:
                user: текущий пользователь
                session: сессия базы данных
            Raises:
                HTTPException: если у пользователя нет прав
        """

        query_element = select(BusinessElement).where(BusinessElement.name == self.business_element)
        result_element = await session.execute(query_element)
        element = result_element.scalar_one_or_none()

        if not element:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Элемент бизнес-логики не найден",
            )

        query_rule = select(AccessRule).where(
            element.id == AccessRule.business_element_id,
            AccessRule.role_id == user.role_id
        )
        result_rule = await session.execute(query_rule)
        rule = result_rule.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Права доступа не найдены",
            )

        permission_value = getattr(rule, self.permission)

        if not permission_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на выполнение этого действия",
            )

        return user