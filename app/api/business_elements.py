from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db.session import get_session
from app.schemas.admin import BusinessElementCreate, BusinessElementRead
from app.models.users import Role
from app.models.rbac import BusinessElement, AccessRule
from app.api.deps import get_admin_user, PermissionChecker


router = APIRouter()
@router.post("/elements", dependencies=[Depends(get_admin_user)], response_model=BusinessElementRead,
             tags=["Бизнес-элементы"])
async def create_business_element(
        element_in: BusinessElementCreate,
        session: AsyncSession = Depends(get_session),
):
    """
        Создаем новый бизнес-элемент

        Args:
            element_in: данные для создания элемента
            session: сессия БД

        Returns:
            BusinessElementRead: созданный элемент
        """

    query = select(BusinessElement).where(BusinessElement.name == element_in.name)
    result = await session.execute(query)

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Элемент {element_in.name} уже существует"
        )

    new_element = BusinessElement(name=element_in.name)
    session.add(new_element)
    await session.flush()
    await session.refresh(new_element)

    roles_result = await session.execute(select(Role))
    roles = roles_result.scalars().all()

    for role in roles:
        is_admin = (role.name == "admin")

        new_rule = AccessRule(
            role_id=role.id,
            business_element_id=new_element.id,
            # все права доступа для админа
            read_permission=is_admin,
            read_all_permissions=is_admin,
            create_permission=is_admin,
            update_permission=is_admin,
            update_all_permissions=is_admin,
            delete_permission=is_admin,
            delete_all_permissions=is_admin
        )
        session.add(new_rule)

    await session.commit()

    return new_element