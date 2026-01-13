from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import Role, User
from app.models.rbac import BusinessElement, AccessRule
from app.core.security import get_password_hash


async def _get_or_create(session: AsyncSession, model, **kwargs):
    """
    Получить или создать объект модели.

    Args:
        session: AsyncSession - сессия базы данных
        model: класс модели
        **kwargs: параметры для поиска или создания объекта

    Returns:
        Объект модели
    """

    # Проверяем, существует ли объект с такими параметрами
    query = select(model).filter_by(**kwargs)
    result = await session.execute(query)
    instance = result.scalar_one_or_none()

    # Если объекта нет, создаем его и добавляем в сессию
    if instance is None:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)

    return instance


async def _create_access_rule_if_not_exists(
    session: AsyncSession,
    role_id: int,
    element_id: int,
    permissions: dict,
):
    """
    Создает правило доступа, если его еще нет

    Args:
        session: AsyncSession - сессия базы данных
        role_id: int - ID роли
        element_id: int - ID элемента бизнес-логики
        permissions: dict - права доступа
    """

    # Проверяем, существует ли правило доступа с такими параметрами
    query = select(AccessRule).where(
        AccessRule.role_id == role_id,
        AccessRule.business_element_id == element_id,
    )
    result = await session.execute(query)
    rule = result.scalar_one_or_none()

    # Если правило не существует, создаем его и добавляем в сессию
    if rule is None:
        rule = AccessRule(role_id=role_id, business_element_id=element_id, **permissions)
        session.add(rule)


async def init_db(session: AsyncSession):
    """Заполняет базу данных ролями и правами доступа"""

    # Заполняем роли
    admin_role = await _get_or_create(session, Role, name="admin")
    manager_role = await _get_or_create(session, Role, name="manager")
    user_role = await _get_or_create(session, Role, name="user")

    # Создаем словарь для быстрого доступа к ролям по имени
    roles_map = {
        "admin": admin_role,
        "manager": manager_role,
        "user": user_role,
    }

    # Заполняем пользователей
    for role_name in ["admin", "manager", "user"]:
        email = f"{role_name}@{role_name}.com"
        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        # Если пользователь с такой ролью не создан, создаем его
        if not existing_user:
            new_user = User(
                email=email,
                hashed_password=await get_password_hash(role_name),
                role_id=roles_map[role_name].id,
                name=role_name.title(),
            )

            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)

    # Создаем словарь для быстрого доступа к правам доступа по имени роли
    permissions_map = {
        "admin": {
            "read_all_permission": True,
            "update_all_permission": True,
            "delete_all_permission": True,
            "create_permission": True,
            "read_permission": True,
            "update_permission": True,
            "delete_permission": True,
        },
        "manager": {
            "read_all_permission": True,
            "update_all_permission": False,
            "delete_all_permission": False,
            "create_permission": True,
            "read_permission": True,
            "update_permission": True,
            "delete_permission": False,
        },
        "user": {
            "read_all_permission": False,
            "update_all_permission": False,
            "delete_all_permission": False,
            "create_permission": False,
            "read_permission": True,
            "update_permission": False,
            "delete_permission": False,
        },
    }
    # Создаем элементы бизнес-логики
    users_element = await _get_or_create(session, BusinessElement, name="users")
    business_element = await _get_or_create(session, BusinessElement, name="business_elements")

    # Заполняем права доступа (админ, пользователь, менеджер)
    for element in [users_element, business_element]:
        await _create_access_rule_if_not_exists(
            session,
            role_id=admin_role.id,
            element_id=element.id,
            permissions=permissions_map["admin"],
        )

        await _create_access_rule_if_not_exists(
            session,
            role_id=manager_role.id,
            element_id=element.id,
            permissions=permissions_map["manager"],
        )

        await _create_access_rule_if_not_exists(
            session,
            role_id=user_role.id,
            element_id=element.id,
            permissions=permissions_map["user"],
        )

    await session.commit()
