from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database (Postgres)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Собираем строку подключения автоматически из переменных.
        Используем asyncpg драйвер.
        """
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Uvicorn
    UVI_PORT: int = 8000
    UVI_HOST: str = "0.0.0.0"

    # Loguru
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "<green>{time:HH:mm}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    LOG_COLORIZE: bool = True

    # Конфигурация Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",  # Читаем из .env
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорируем лишние переменные в .env
    )


# Создаем единственный экземпляр настроек
settings = Settings()
