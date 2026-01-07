from pydantic import BaseModel


class AccessRuleUpdate(BaseModel):
    read_permission: bool | None = None
    read_all_permissions: bool | None = None
    create_permission: bool | None = None
    update_permission: bool | None = None
    update_all_permissions: bool | None = None
    delete_permission: bool | None = None
    delete_all_permissions: bool | None = None


class UserRoleUpdate(BaseModel):
    role_id: int


class BusinessElementCreate(BaseModel):
    name: str

class BusinessElementRead(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True