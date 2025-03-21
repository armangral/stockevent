from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.crud.holdings import update_holding
from app.crud.watchlists import create_watchlist, delete_symbol_from_watchlist, delete_watchlist, get_current_price, get_current_price_stock, get_holding_by_symbol_crud, get_stock_data, get_total_value_of_all_assets_crud, get_total_value_of_all_assets_crud_gbp, get_user_watchlist_id_crud, get_watchlist_by_id, get_watchlist_by_symbol
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


@router.put("/watchlist/{symbol}/holding")
async def edit_holding(
    symbol: str,
    holding_data: HoldingCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    watchlist = await get_watchlist_by_symbol(db, user.id, symbol)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    if watchlist.type == 'stocks':
        current_price = await get_current_price_stock(f"{watchlist.symbol}")
    else:
        current_price = await get_current_price(f"{watchlist.symbol}")
    holding_data = await update_holding(db, watchlist.id, holding_data,current_price)
    holding_data_dict = vars(holding_data)
    pnl = (current_price-holding_data_dict['average_cost'])*holding_data_dict['shares']
    holding_data_dict['pnl'] =pnl
    total_value = current_price * holding_data_dict['shares']
    holding_data_dict['total_value'] = total_value
    return holding_data


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


@router.get("/watchlist/symbols")
async def get_user_watchlist(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    watchlists =  await get_user_watchlist_symbols_crud(db, user.id)
    watchlist_data = []
    for watchlist in watchlists:
        current_data = await get_stock_data(f"{watchlist.symbol}",watchlist.type)
        watchlist_data.append(current_data)
    return watchlist_data
    
    # holding_data_dict = vars(holdings)
    # pnl = (current_price - holding_data_dict["average_cost"]) * holding_data_dict[
    #     "shares"
    # ]
    # holding_data_dict["pnl"] = pnl
    # total_value = current_price * holding_data_dict["shares"]
    # holding_data_dict["total_value"] = total_value
    # return holding_data_dict


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
    holdings = await get_holding_by_symbol_crud(db, user.id, symbol)
    if not holdings:
        return []
    watchlist = await get_watchlist_by_id(db, holdings.watchlist_id)
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")

    if watchlist.type == 'stocks':
        current_price = await get_current_price_stock(f"{watchlist.symbol}")
    else:
        current_price = await get_current_price(f"{watchlist.symbol}")
    holding_data_dict = vars(holdings)
    pnl = (current_price - holding_data_dict["average_cost"]) * holding_data_dict[
        "shares"
    ]
    holding_data_dict["pnl"] = pnl
    total_value = current_price * holding_data_dict["shares"]
    holding_data_dict["total_value"] = total_value
    return holding_data_dict


#get total value of all the assests not just one symbol
@router.get("/totalvalue")
async def get_total_value_of_all_assets(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    ):
    return await get_total_value_of_all_assets_crud(db, user.id)

@router.get("/totalvalue-gbp")
async def get_total_value_of_all_assets_gbp(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await get_total_value_of_all_assets_crud_gbp(db, user.id)
