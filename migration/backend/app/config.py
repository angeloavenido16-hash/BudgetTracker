"""app/config.py — environment-driven settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://budget:budget@localhost:5432/budget_tracker"

    # Auth
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    APP_USERNAME: str = "admin"
    APP_PASSWORD: str = "change-me"

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"


settings = Settings()
