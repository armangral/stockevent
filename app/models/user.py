from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

from app.models.mixin import SharedMixin



class User(Base,SharedMixin):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[LargeBinary] = mapped_column(LargeBinary)
    password_salt: Mapped[LargeBinary] = mapped_column(LargeBinary)
    is_super_admin: Mapped[bool] = mapped_column(Boolean)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # # Social login fields
    social_id: Mapped[str] = mapped_column(String(255), nullable=True)
    social_provider: Mapped[str] = mapped_column(String(50), nullable=True)