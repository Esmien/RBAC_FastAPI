from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.schemas.admin import BusinessElementCreate, BusinessElementRead
from app.models.users import Role, User
from app.models.rbac import BusinessElement, AccessRule
from app.api.deps import get_admin_user, PermissionChecker

router = APIRouter()


@router.post(
    "/elements",
    response_model=BusinessElementRead,
)
async def create_business_element(
    element_in: BusinessElementCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(PermissionChecker("business_elements", "create_permission")),
):
    """
    Создаем новый бизнес-элемент

    Args:
        element_in: данные для создания элемента
        session: сессия БД
        _: текущий пользователь, проверка прав доступа

    Returns:
        BusinessElementRead: созданный элемент
    """

    # проверяем, что элемент с таким именем еще не существует
    query = select(BusinessElement).where(BusinessElement.name == element_in.name)
    result = await session.execute(query)

    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Элемент {element_in.name} уже существует"
        )

    # создаем новый элемент
    new_element = BusinessElement(name=element_in.name)
    session.add(new_element)
    await session.flush()
    await session.refresh(new_element)

    # создаем для него правила доступа для всех ролей
    roles_result = await session.execute(select(Role))
    roles = roles_result.scalars().all()

    for role in roles:
        is_admin = role.name == "admin"

        new_rule = AccessRule(
            role_id=role.id,
            business_element_id=new_element.id,
            # все права доступа для админа
            read_permission=is_admin,
            read_all_permission=is_admin,
            create_permission=is_admin,
            update_permission=is_admin,
            update_all_permission=is_admin,
            delete_permission=is_admin,
            delete_all_permission=is_admin,
        )
        session.add(new_rule)

    await session.commit()

    return new_element


@router.get("/elements", response_model=list[BusinessElementRead])
async def get_business_elements(
        session: AsyncSession = Depends(get_session),
        _: User = Depends(PermissionChecker("business_elements", "read_all_permission")),
):
    """
    Получаем список бизнес-элементов

    Args:
        session: сессия БД
        _: текущий пользователь, проверка прав доступа

    Returns:
        list[BusinessElementRead]: список всех бизнес-элементов
    """

    query = select(BusinessElement)
    result = await session.execute(query)
    elements = result.scalars().all()

    if elements:
        return elements

    return []
