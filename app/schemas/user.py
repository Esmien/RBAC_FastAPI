from pydantic import BaseModel, EmailStr, Field, model_validator


class RoleBase(BaseModel):
    name: str


class RoleRead(RoleBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    name: str = "Пользователь"  # имя
    surname: str | None = None  # отчество
    last_name: str | None = None  # фамилия


# Для безопасной регистрации пользователя
class UserRegister(UserBase):
    password: str = Field(..., min_length=3, max_length=72)
    repeat_password: str = Field(..., min_length=3, max_length=72)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Пароли не совпадают!")
        return self


# Для создания пользователя админом
class UserCreate(UserRegister):
    role_id: int | None = None
    is_active: bool = True

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "name": "Иван",
                    "surname": "Иванович",
                    "last_name": "Иванов",
                    "password": "secret_password",
                    "repeat_password": "secret_password",
                    "role_id": 2,
                    "is_active": True,
                }
            ]
        }
    }


class UserRead(UserBase):
    id: int
    is_active: bool
    role: RoleRead

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    surname: str | None = None
    last_name: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str