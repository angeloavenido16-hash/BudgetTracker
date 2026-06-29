"""
tests/conftest.py — shared pytest setup.

Ensures the required environment variables exist BEFORE any test imports
app.config (which reads them), so the suite runs without a .env file and
against an in-memory SQLite DB by default.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("APP_USERNAME", "admin")
os.environ.setdefault("APP_PASSWORD", "admin")
