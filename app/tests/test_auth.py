import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(ac: AsyncClient):
    """Проверка регистрации пользователя"""

    user_data = {
        "email": "test@example.com",
        "password": "strongpassword123",
        "repeat_password": "strongpassword123",
        "name": "Test User",
        "surname": "Testov",
        "last_name": "Testovich",
    }

    response = await ac.post("/users/register", json=user_data)

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "role" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_login_user(ac: AsyncClient, setup_db):
    """Проверка логина пользователя"""

    user_login = {
        "username": "user@user.com",
        "password": "user",
    }

    response = await ac.post("/users/login", data=user_login)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "token_type" in data and data["token_type"] == "bearer"
