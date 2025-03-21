from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base
from sqlalchemy.orm import relationship

from app.models.mixin import SharedMixin




# Model for Watchlist
class Watchlist(Base, SharedMixin):
    __tablename__ = "watchlists"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    holding: Mapped["Holding"] = relationship("Holding", back_populates="watchlist", uselist=False)