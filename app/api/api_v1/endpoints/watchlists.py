from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.crud.holdings import update_holding
from app.crud.watchlists import create_watchlist, delete_symbol_from_watchlist, delete_watchlist, get_holding_by_symbol_crud, get_user_watchlist_id_crud, get_watchlist_by_id, get_watchlist_by_symbol
from app.schemas.holdings import HoldingCreate, HoldingResponse
from app.schemas.watchlists import WatchlistCreate, WatchlistResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_session
from app.crud.watchlists import get_user_watchlist_symbols_crud 

router = APIRouter()


@router.post("/watchlist")
async def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await create_watchlist(db, user.id, watchlist_data)
    return f"symbol {watchlist_data.symbol} has been added to watchlist "


@router.put("/watchlist/{symbol}/holding", response_model=HoldingResponse)
async def edit_holding(
    symbol: str,
    holding_data: HoldingCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    watchlist = await get_watchlist_by_symbol(db, user.id, symbol)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    return await update_holding(db, watchlist.id, holding_data)


# @router.put("/watchlist/{watchlist_id}/holding", response_model=HoldingResponse)
# async def edit_holding(
#     watchlist_id: UUID,
#     holding_data: HoldingCreate,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     watchlist = get_watchlist_by_id(db,watchlist_id)
#     if not watchlist:
#         return HTTPException(status_code=404,detail="Watchlist not found")
#     return await update_holding(db, watchlist_id, holding_data)


# @router.delete("/watchlist/{watchlist_id}")
# async def remove_from_watchlist(
#     watchlist_id: UUID,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     return await delete_watchlist(db, watchlist_id)
@router.delete("/watchlist/{watchlist_id}/{symbol}")
async def remove_symbol_from_watchlist(
    watchlist_id: UUID,
    symbol: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await delete_symbol_from_watchlist(db, watchlist_id, user.id, symbol)


@router.get("/watchlist/symbols", response_model=List[str])
async def get_user_watchlist(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_user_watchlist_symbols_crud(db, user.id)


@router.get("/watchlistid")
async def get_user_watchlist_id(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    watchlist_id =  await get_user_watchlist_id_crud(db, user.id)
    if not watchlist_id:
        return HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist_id


@router.get("/watchlist/{symbol}/holding")
async def get_holding_details(
    symbol: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_holding_by_symbol_crud(db, user.id, symbol)