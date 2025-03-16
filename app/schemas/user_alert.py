from uuid import UUID
from pydantic import BaseModel, EmailStr


class UserAlertCreate(BaseModel):
    email: EmailStr
    symbol: str
    target_price: float


class UserAlertResponse(BaseModel):
    id: UUID
    email: str
    symbol: str
    target_price: float
    is_active: bool

    class Config:
        orm_mode = True
