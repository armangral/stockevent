
from typing import List
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holdings import Holding
from app.models.watchlists import Watchlist
from app.schemas.holdings import HoldingResponse
from app.schemas.watchlists import WatchlistCreate



# CRUD Operations
async def create_watchlist(db: AsyncSession,user_id:UUID, watchlist_data: WatchlistCreate):
    existing_watchlist = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.symbol == watchlist_data.symbol,
        )
    )
    if existing_watchlist.scalar():
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")

    watchlist = Watchlist(**watchlist_data.dict(),user_id = user_id)
    db.add(watchlist)
    await db.flush()
    return watchlist




async def get_watchlist_by_id(db: AsyncSession, watchlist_id: int) -> Watchlist | None:
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    return result.scalar()


async def delete_watchlist(db: AsyncSession, watchlist_id: int):
    result = await db.execute(select(Watchlist).filter(Watchlist.id == watchlist_id))
    watchlist = result.scalar()
    if watchlist:
        await db.execute(delete(Watchlist).where(Watchlist.id == watchlist_id))
        await db.commit()
    return watchlist


async def get_user_watchlist_symbols_crud(db: AsyncSession, user_id: UUID) -> List[str]:
    query = select(Watchlist.symbol).where(Watchlist.user_id == user_id)
    result = await db.execute(query)
    return [row[0] for row in result.fetchall()]

async def get_user_watchlist_id_crud(db: AsyncSession, user_id: UUID) -> UUID | None:
    query = select(Watchlist.id).where(Watchlist.user_id == user_id)
    result = await db.execute(query)
    watchlist_id = result.scalar_one_or_none()  # Fetch only one result or None
    return watchlist_id


async def get_holding_by_symbol_crud(
    db: AsyncSession, user_id: UUID, symbol: str
) -> HoldingResponse | None:
    query = (
        select(Holding)
        .join(Watchlist, Holding.watchlist_id == Watchlist.id)
        .where(Watchlist.user_id == user_id, Watchlist.symbol == symbol)
    )
    result = await db.execute(query)
    holding = result.scalar_one_or_none()
    if not holding:
        return None
    return HoldingResponse(
        symbol=symbol,
        shares=holding.shares,
        avg_cost=holding.average_cost,
        total_pnl=holding.total_pnl,
        total_value=holding.total_value,
    )


async def delete_symbol_from_watchlist(
    db: AsyncSession, watchlist_id: UUID, user_id: UUID, symbol: str
):
    # Check if the watchlist exists and belongs to the user
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id, Watchlist.user_id == user_id
        )
    )
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        raise HTTPException(
            status_code=404, detail="Watchlist not found or does not belong to user"
        )

    # Find and delete the symbol from this watchlist
    delete_query = delete(Watchlist).where(
        Watchlist.id == watchlist_id, Watchlist.symbol == symbol
    )
    result = await db.execute(delete_query)

    if result.rowcount == 0:  # If no rows were deleted, the symbol was not found
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")

    await db.commit()
    return {"message": f"Symbol '{symbol}' removed from watchlist"}

async def get_watchlist_by_symbol(db: AsyncSession, user_id: UUID, symbol: str):
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user_id, Watchlist.symbol == symbol
        )
    )
    return result.scalar_one_or_none()
