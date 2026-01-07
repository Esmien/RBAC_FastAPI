from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db.session import get_session
from app.schemas.user import UserRead
from app.models.users import User
from app.api.deps import get_current_user, PermissionChecker


router = APIRouter()

@router.get("/me", response_model=UserRead)
async def get_me(
        current_user: User = Depends(get_current_user)
):
    """
        Проверка текущего пользователя

        Args:
            current_user: текущий пользователь
        Returns:
            UserRead: пользователь
    """
    return current_user

@router.get("/users", response_model=list[UserRead])
async def get_users(
        session: AsyncSession = Depends(get_session),
        _: User = Depends(PermissionChecker(business_element="users", permission="read_all_permissions"))
):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()