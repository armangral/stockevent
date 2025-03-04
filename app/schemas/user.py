from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    first_name: str
    last_name: str
    username: EmailStr
    #role: UserRole


class UserCreate(UserBase):
    password: str

class UserCreateWithAdmin(UserCreate):
    pass

class UserOut(UserBase):
    id: uuid.UUID
    is_super_admin: Optional[bool]

    class Config:
        orm_mode = True


class UserOutForadmin(UserBase):
    id: uuid.UUID
    is_super_admin: Optional[bool]
    is_active: Optional[bool]
    email_verified: Optional[bool]
    last_login: Optional[datetime]

    class Config:
        orm_mode = True


class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str