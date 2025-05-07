from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base
from app.models.mixin import SharedMixin


class UserAlert(Base, SharedMixin):
    __tablename__ = "user_alerts"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
