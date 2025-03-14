from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holdings import Holding
from app.schemas.holdings import HoldingCreate





async def update_holding(
    db: AsyncSession, watchlist_id: UUID, holding_data: HoldingCreate
):
    result = await db.execute(
        select(Holding).filter(Holding.watchlist_id == watchlist_id)
    )
    holding = result.scalar()

    if holding:
        total_shares = holding.shares + holding_data.shares
        total_cost = (holding.shares * holding.average_cost) + (
            holding_data.shares * holding_data.average_cost
        )
        holding.shares = total_shares
        holding.average_cost = total_cost / total_shares if total_shares > 0 else 0.0
    else:
        holding = Holding(
            watchlist_id=watchlist_id,
            shares=holding_data.shares,
            average_cost=holding_data.average_cost,
        )
        db.add(holding)

    await db.commit()
    await db.refresh(holding)
    return holding


# async def update_holding(
#     db: AsyncSession, watchlist_id: UUID, holding_data: HoldingCreate
# ):
#     result = await db.execute(
#         select(Holding).filter(Holding.watchlist_id == watchlist_id)
#     )
#     holding = result.scalar()

#     if holding:
#         total_shares = holding.shares + holding_data.shares
#         total_cost = (holding.shares * holding.average_cost) + (
#             holding_data.shares * holding_data.average_cost
#         )
#         holding.shares = total_shares
#         holding.average_cost = total_cost / total_shares if total_shares > 0 else 0.0
#     else:
#         holding = Holding(
#             watchlist_id=watchlist_id,
#             shares=holding_data.shares,
#             average_cost=holding_data.average_cost,
#         )
#         db.add(holding)

#     await db.commit()
#     await db.refresh(holding)
#     return holding
