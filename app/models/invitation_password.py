from datetime import datetime, timedelta

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixin import SharedMixin


class InvitationPassword(Base, SharedMixin):
    __tablename__ = "invitation_password"

    email: Mapped[str] = mapped_column(String(255), nullable=False)

    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
