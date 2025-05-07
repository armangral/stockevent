from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base
from sqlalchemy.orm import relationship

from app.models.mixin import SharedMixin
from app.models.watchlists import Watchlist


class Holding(Base, SharedMixin):
    __tablename__ = "holdings"

    watchlist_id: Mapped[int] = mapped_column(
        ForeignKey("watchlists.id"), nullable=False
    )
    shares: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    average_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    @property
    def total_pnl(self) -> float:
        return (self.current_price - self.average_cost) * self.shares

    @property
    def total_value(self) -> float:
        return self.shares * self.current_price

    watchlist: Mapped["Watchlist"] = relationship("Watchlist", back_populates="holding")