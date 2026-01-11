import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_rbac(ac: AsyncClient, setup_db):
    admin_data = {"username": "admin@admin.com", "password": "admin"}

    response = await ac.post("/users/login", data=admin_data)

    assert response.status_code == 200

    data = response.json()

    token = data["access_token"]
    element_name = "test_element"

    response = await ac.post(
        "/business-elements/elements",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": element_name},
    )

    assert response.status_code == 200
    assert response.json()["name"] == element_name


async def test_user_cannot_create_business_element(ac: AsyncClient, setup_db):
    user_data = {"username": "user@user.com", "password": "user"}

    response = await ac.post("/users/login", data=user_data)

    assert response.status_code == 200

    data = response.json()

    token = data["access_token"]
    element_name = "test_element"

    response = await ac.post(
        "/business-elements/elements",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": element_name},
    )

    assert response.status_code == 403
