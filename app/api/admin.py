from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.database.session import get_session
from app.schemas.user import UserRead, UserCreate, UserChangeStatus
from app.schemas.admin import AccessRuleUpdate, UserRoleUpdate
from app.models.users import User, Role
from app.models.rbac import AccessRule
from app.api.deps import get_admin_user, get_user_by_id

router = APIRouter()


@router.post(
    "/users/create",
    dependencies=[Depends(get_admin_user)],
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя через админку",
)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Регистрация пользователя админом.
    Админ может назначать роль, отличную от 'user' при регистрации.

    Args:
        user_in: данные пользователя
        session: сессия БД

    Raises:
        HTTPException:
            Пользователь с таким email уже существует (400)
            Роль с таким id не найдена (404)
            Базовая роль 'user' не найдена (500)

    Returns:
        UserRead: Пользователь
    """

    # Проверяем, существует ли пользователь с таким email
    query = select(User).where(User.email == user_in.email)
    result = await session.execute(query)

    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    role_id = user_in.role_id

    if role_id:
        # Проверяем, существует ли роль с таким id
        role_result = await session.execute(select(Role).where(Role.id == role_id))

        if not role_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Роль с id {role_id} не найдена")
    else:
        user_role = await session.execute(select(Role).where(Role.name == "user"))
        role_obj = user_role.scalar_one_or_none()

        # Если роль 'user' не найдена, то возвращаем ошибку сервера, так как она должна быть
        if not role_obj:
            raise HTTPException(status_code=500, detail="Базовая роль 'user' не найдена")
        role_id = role_obj.id

    # Создаем нового пользователя
    new_user = User(
        email=str(user_in.email),
        hashed_password=await get_password_hash(user_in.password),
        name=user_in.name,
        surname=user_in.surname,
        last_name=user_in.last_name,
        role_id=role_id,
        is_active=user_in.is_active,
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.delete(
    "/users/soft_delete/{user_id}",
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    summary="'Мягкое' удаление пользователя по ID",
)
async def soft_delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Удаление пользователя

    Args:
        user_id: id пользователя для удаления
        session: сессия БД

    Raises:
        HTTPException: Пользователь уже удален (409)

    Returns:
        UserRead: Удаленный пользователь
    """

    user = await get_user_by_id(user_id, session)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже удален")

    user.is_active = False

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.delete(
    "/users/total_delete/{user_id}",
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_200_OK,
    response_model=UserChangeStatus,
    summary="Полное удаление пользователя",
)
async def total_delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Полное удаление пользователя

    Args:
        user_id: id пользователя для удаления
        session: сессия БД

    Raises:
        HTTPException: Пользователь не найден (404)

    Returns:
        UserChangeStatus: данные удаленного пользователя
    """

    query = delete(User).where(User.id == user_id).returning(User)
    result = await session.execute(query)
    deleted_user = result.scalar_one_or_none()

    if not deleted_user:
        logger.warning(f"Пользователь с id {user_id} не найден")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с id {user_id} не найден",
        )

    logger.info(f"Пользователь с id {user_id} удален")
    await session.commit()

    return UserChangeStatus(message=f"Пользователь с id {user_id} удален", user=deleted_user)


@router.patch(
    "/users/role/{user_id}",
    dependencies=[Depends(get_admin_user)],
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Изменение роли пользователя",
)
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
        HTTPException: Пользователь не найден (404)

    Returns:
        UserRead: Обновленный пользователь
    """

    # Проверяем, существует ли пользователь
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, существует ли роль
    query_role = select(Role).where(Role.id == role_update.role_id)
    result_role = await session.execute(query_role)

    if result_role.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    # Обновляем роль пользователя
    user.role_id = role_update.role_id
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.patch(
    "/permissions/{role_id}/{element_id}",
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_200_OK,
    summary="Изменение прав доступа для роли",
)
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

    Raises:
        HTTPException: Правило доступа не найдено (404)

    Returns:
        json: {"message": "Права доступа обновлены"}
    """

    # Проверяем, существует ли правило доступа
    query = select(AccessRule).where(AccessRule.role_id == role_id, AccessRule.business_element_id == element_id)
    result = await session.execute(query)
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Правило доступа не найдено. Проверьте id роли и элемента",
        )

    # Обновляем права доступа
    update_data = rule_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    return {"message": "Права доступа обновлены"}
