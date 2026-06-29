"""app/config.py — environment-driven settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    # Local dev defaults to SQLite (no server needed). For Postgres, set
    # DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_URL: str = "sqlite+aiosqlite:///./budget_tracker.db"

    # Auth
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # Seed admin — used only when the DB has no users at all.
    # After first login, change the password via the admin panel.
    # Remove these defaults by setting SEED_USERNAME / SEED_PASSWORD in .env.
    SEED_USERNAME: str = "admin"
    SEED_PASSWORD: str = "admin"

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"


settings = Settings()
