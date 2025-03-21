from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.watchlists import get_current_price
from app.models.holdings import Holding
from app.models.watchlists import Watchlist
from app.schemas.holdings import HoldingCreate





# # async def update_holding(
# #     db: AsyncSession, watchlist_id: UUID, holding_data: HoldingCreate, current_price: float
# # ):
# #     result = await db.execute(
# #         select(Holding).filter(Holding.watchlist_id == watchlist_id)
# #     )
# #     holding = result.scalar()

# #     if holding:
# #         print("already hold something")
# #         total_shares = holding_data.shares
# #         average_cost_now = current_price
# #         total_cost = (holding.shares * holding.average_cost) + (
# #             holding_data.shares * average_cost_now
# #         )
# #         holding.shares = total_shares
# #         holding.average_cost = total_cost / total_shares if total_shares > 0 else 0.0
#     else:
#         holding = Holding(
#             watchlist_id=watchlist_id,
#             shares=holding_data.shares,
#             average_cost=current_price
#         )
#         db.add(holding)

#     await db.commit()
#     await db.refresh(holding)
#     return holding


async def update_holding(
    db: AsyncSession,
    watchlist_id: UUID,
    holding_data: HoldingCreate,
    current_price: float,
):
    result = await db.execute(
        select(Holding).filter(Holding.watchlist_id == watchlist_id)
    )
    holding = result.scalar()

    if holding:
        print("already hold something")

        # Calculate new shares added
        new_shares = holding_data.shares - holding.shares

        # Only update if new shares are added
        if new_shares > 0:
            # Calculate new total cost and average price
            total_cost = (holding.shares * holding.average_cost) + (
                new_shares * current_price
            )
            holding.shares = holding_data.shares  # Update to new total shares
            holding.average_cost = (
                total_cost / holding.shares if holding.shares > 0 else 0.0
            )
    else:
        # If no holding exists, create a new one
        holding = Holding(
            watchlist_id=watchlist_id,
            shares=holding_data.shares,
            average_cost=current_price,
        )
        db.add(holding)

    await db.commit()
    await db.refresh(holding)
    return holding
