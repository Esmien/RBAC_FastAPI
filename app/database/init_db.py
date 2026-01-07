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

    query = select(model).filter_by(**kwargs)
    result = await session.execute(query)
    instance = result.scalar_one_or_none()

    if instance is None:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)

    return instance


async def _create_access_rule_if_not_exists(
        session: AsyncSession,
        role_id: int, element_id: int, permissions: dict
):
    """
        Создает правило доступа, если его еще нет

        Args:
            session: AsyncSession - сессия базы данных
            role_id: int - ID роли
            element_id: int - ID элемента бизнес-логики
            permissions: dict - права доступа
        """

    query = select(AccessRule).where(
        AccessRule.role_id == role_id,
        AccessRule.business_element_id == element_id
    )
    result = await session.execute(query)
    rule = result.scalar_one_or_none()

    if rule is None:
        rule = AccessRule(
            role_id=role_id,
            business_element_id=element_id,
            **permissions
        )
        session.add(rule)


async def init_db(session: AsyncSession):
    """ Заполняет базу данных ролями и правами доступа """

    # Заполняем роли
    admin_role = await _get_or_create(session, Role, name="admin")
    user_role = await _get_or_create(session, Role, name="user")
    manager_role = await _get_or_create(session, Role, name="manager")

    # Заполняем пользователей (админ)
    query = select(User).filter_by(email="admin@admin.com")
    result = await session.execute(query)
    admin_user = result.scalar_one_or_none()

    # Если амин не создан, создаем его
    if not admin_user:
        admin_user = User(
            email="admin@admin.com",
            hashed_password=get_password_hash("admin"),
            role_id=admin_role.id,
            name="Admin"
        )
        session.add(admin_user)
        await session.flush()  # Чтобы получить ID пользователя для дальнейших связей
        await session.refresh(admin_user)

    # Создаем элемент бизнес-логики "users"
    users_element = await _get_or_create(session, BusinessElement, name="users")

    # Заполняем права доступа (админ, пользователь, менеджер)
    await _create_access_rule_if_not_exists(
        session,
        role_id=admin_role.id,
        element_id=users_element.id,
        permissions={
            "read_all_permissions": True,
            "update_all_permissions": True,
            "delete_all_permissions": True,
            "create_permission": True,
            "read_permission": True,
            "update_permission": True,
            "delete_permission": True,
        }
    )

    await _create_access_rule_if_not_exists(
        session,
        role_id=manager_role.id,
        element_id=users_element.id,
        permissions={
            "read_all_permissions": True,
            "update_all_permissions": False,
            "delete_all_permissions": False,
            "create_permission": False,
            "read_permission": True,
            "update_permission": False,
            "delete_permission": False,
        }
    )

    await _create_access_rule_if_not_exists(
        session,
        role_id=user_role.id,
        element_id=users_element.id,
        permissions={
            "read_all_permissions": False,
            "update_all_permissions": False,
            "delete_all_permissions": False,
            "create_permission": False,
            "read_permission": True,
            "update_permission": False,
            "delete_permission": False,
        }
    )

    await session.commit()