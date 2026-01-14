from pydantic import BaseModel, ConfigDict


class RBACPermissions(BaseModel):
    read_permission: bool | None = None
    read_all_permission: bool | None = None
    create_permission: bool | None = None
    update_permission: bool | None = None
    update_all_permission: bool | None = None
    delete_permission: bool | None = None
    delete_all_permission: bool | None = None

    model_config = ConfigDict(extra='forbid')