from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class SharedMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    time_created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow,nullable=True)
    time_updated: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow,nullable=True)
    is_deleted: Mapped[bool] = mapped_column(nullable=True)
