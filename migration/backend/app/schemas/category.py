"""Category schemas — expense category dropdown list."""
from __future__ import annotations

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
