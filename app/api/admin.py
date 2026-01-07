from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db.session import get_session
from app.schemas.user import UserRead
from app.schemas.admin import AccessRuleUpdate, UserRoleUpdate, BusinessElementCreate, BusinessElementRead
from app.models.users import User, Role
from app.models.rbac import BusinessElement, AccessRule
from app.api.deps import get_admin_user


router = APIRouter()

@router.patch("/users/{user_id}/role", dependencies=[Depends(get_admin_user)], response_model=UserRead)
async def update_user_role(
        user_id: int,
        role_update: UserRoleUpdate,
        session: AsyncSession = Depends(get_session),
):
    """
        Меняем роль пользователя

        Args:
            user_id: id пользователя
            role_update: данные для обновления роли
            session: сессия

        Raises:
            404: Пользователь не найден, Роль не найдена

        Returns:
            UserRead: Обновленный пользователь
        """

    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    query_role = select(Role).where(Role.id == role_update.role_id)
    result_role = await session.execute(query_role)

    if result_role.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404,
            detail="Роль не найдена"
        )

    user.role_id = role_update.role_id
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.patch("/permissions/{role_id}/{element_id}", dependencies=[Depends(get_admin_user)])
async def update_access_rule(
        role_id: int,
        element_id: int,
        rule_update: AccessRuleUpdate,
        session: AsyncSession = Depends(get_session),
):
    """
        Меняем права доступа

        Args:
            role_id: id роли
            element_id: id элемента
            rule_update: данные для обновления прав доступа
            session: сессия БД
        """

    query = select(AccessRule).where(
        AccessRule.role_id == role_id,
        AccessRule.business_element_id == element_id
    )
    result = await session.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Правило доступа не найдено. Проверьте id роли и элемента"
        )

    update_data = rule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    return {"message": "Права доступа обновлены"}