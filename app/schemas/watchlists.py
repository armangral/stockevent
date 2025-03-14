from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.schemas.holdings import HoldingResponse


class WatchlistCreate(BaseModel):
    symbol: str


class WatchlistResponse(BaseModel):
    id: UUID
    user_id: UUID
    symbol: str
    holding: HoldingResponse | None = None

    class Config:
        from_attributes = True