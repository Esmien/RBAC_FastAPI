from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict


class RoleBase(BaseModel):
    name: str


class RoleRead(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    name: str = Field(..., examples=["Иван"])  # имя
    surname: str | None = Field(default=None, examples=["Иванович"])  # отчество
    last_name: str | None = Field(default=None, examples=["Иванов"])  # фамилия


class UserRead(UserBase):
    id: int
    is_active: bool
    role: RoleRead

    model_config = ConfigDict(from_attributes=True)


# Для безопасной регистрации пользователя
class UserRegister(UserBase):
    password: str = Field(..., min_length=3, max_length=72, examples=["secret_password"])
    repeat_password: str = Field(..., min_length=3, max_length=72, examples=["secret_password"])

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Пароли не совпадают!")
        return self


class UserChangeStatus(BaseModel):
    message: str
    user: UserRead


# Для создания пользователя админом
class UserCreate(UserRegister):
    role_id: int = Field(..., examples=[3])
    is_active: bool = Field(default=True, examples=[True])


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    name: str | None = None
    surname: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(extra="forbid")


class Token(BaseModel):
    access_token: str
    token_type: str
