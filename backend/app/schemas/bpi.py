"""BPI balance schemas — bank balance snapshots."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BpiUpdate(BaseModel):
    balance: float


class BpiBalance(BaseModel):
    balance: float
    recorded_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
