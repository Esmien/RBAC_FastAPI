from fastapi import APIRouter, Depends
from app.schemas.user import UserRead
from app.models.users import User
from app.api.deps import get_current_user


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