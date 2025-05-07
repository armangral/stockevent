from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

# Import only the necessary CRUD functions after refactoring
from app.crud.holdings import update_holding
from app.crud.watchlists import (
    create_watchlist,
    delete_symbol_from_watchlist,
    delete_watchlist,  # Keep if still used, though delete_watchlist_and_holding might be preferred
    delete_watchlist_and_holding,
    # Removed get_current_price, get_current_price_stock
    # Removed get_stock_data_with_watchid
    get_holding_by_symbol_crud,
    get_total_value_of_all_assets_crud,
    get_total_value_of_all_assets_crud_gbp,
    get_user_watchlist_id_crud,
    get_watchlist_by_id,
    get_watchlist_by_symbol,
    # Import the new batched display data fetcher
    fetch_watchlist_display_data_batched,
    # Import the single item data fetcher (now includes caching/retries)
    get_stock_data,
)
from app.schemas.holdings import HoldingCreate, HoldingResponse
from app.schemas.watchlists import (
    WatchlistCreate,
    WatchlistResponse,
)  # WatchlistResponse might need adjustment if it included nested Holding details directly and the new fetcher doesn't provide that structure
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_session
# from app.crud.watchlists import get_user_watchlist_symbols_crud # This CRUD function is used internally by fetch_watchlist_display_data_batched, no need to import here

router = APIRouter()

# --- Endpoints ---


@router.post("/watchlist")
async def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Adds a new symbol to the user's watchlist.
    """
    await create_watchlist(db, user.id, watchlist_data)
    return {"detail": f"Symbol '{watchlist_data.symbol}' has been added to watchlist"}


@router.put("/watchlist/{symbol}/holding")
async def edit_holding(
    symbol: str,
    holding_data: HoldingCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """
    Adds or updates holding information for a symbol in the user's watchlist.
    Requires fetching the current price to calculate average cost for new shares.
    """
    # 1. Get the watchlist entry for the symbol
    watchlist = await get_watchlist_by_symbol(db, user.id, symbol)
    if not watchlist:
        raise HTTPException(
            status_code=404, detail="Watchlist entry not found for this symbol"
        )

    # 2. Get the current price for this specific symbol using the cached single fetcher
    # Use the refactored get_stock_data, which handles both stocks and crypto and includes caching/retries
    current_data = await get_stock_data(watchlist.symbol, watchlist.type)
    current_price = current_data.get("price")

    if current_price is None or current_price == 0.0 or current_price == "N/A":
        # Cannot calculate average cost or total value if price is unavailable
        raise HTTPException(
            status_code=500, detail=f"Could not fetch current price for {symbol}"
        )

    # 3. Update the holding using the fetched current price
    holding_entry = await update_holding(db, watchlist.id, holding_data, current_price)

    if not holding_entry:
        # update_holding should ideally return the holding object or raise error,
        # but let's add a check just in case it returns None unexpectedly
        raise HTTPException(status_code=500, detail="Failed to update holding")

    # 4. Prepare the response data including calculated PNL and total value
    # Access attributes directly from the ORM object
    pnl = (current_price - holding_entry.average_cost) * holding_entry.shares
    total_value = current_price * holding_entry.shares

    # Return a dictionary representing the holding details + calculated values
    # You might want to define a Pydantic schema for this combined response
    response_data = {
        "id": holding_entry.id,  # Include Holding ID
        "watchlist_id": holding_entry.watchlist_id,  # Include Watchlist ID
        "shares": holding_entry.shares,
        "average_cost": holding_entry.average_cost,
        # Include current price and calculated values
        "current_price": current_price,
        "pnl": round(pnl, 2),
        "total_value": round(total_value, 2),
        # You might want to include symbol and type from the watchlist for clarity
        "symbol": watchlist.symbol,
        "type": watchlist.type,
    }

    return response_data


# @router.put("/watchlist/{watchlist_id}/holding", response_model=HoldingResponse)
# async def edit_holding(...): # This endpoint seems to use watchlist_id directly, original logic used symbol.
# Keeping the /watchlist/{symbol}/holding pattern as it seems more user-friendly.
# If you need to keep both, adjust this one to use get_stock_data and update_holding similarly.
# @router.put("/watchlist/{watchlist_id}/holding", response_model=HoldingResponse)
# async def edit_holding_by_id(
#     watchlist_id: UUID,
#     holding_data: HoldingCreate,
#     user=Depends(get_current_user), # Need user to verify ownership if watchlist_id isn't globally unique per user or exposed without auth check
#     db: AsyncSession = Depends(get_session),
# ):
#     watchlist = await get_watchlist_by_id(db, watchlist_id)
#     if not watchlist or str(watchlist.user_id) != str(user.id): # Add ownership check
#         raise HTTPException(status_code=404, detail="Watchlist not found or does not belong to user")

#     # Fetch current price similar to the symbol-based endpoint
#     current_data = await get_stock_data(watchlist.symbol, watchlist.type)
#     current_price = current_data.get("price")

#     if current_price is None or current_price == 0.0 or current_price == "N/A":
#          raise HTTPException(status_code=500, detail=f"Could not fetch current price for {watchlist.symbol}")

#     holding_entry = await update_holding(db, watchlist_id, holding_data, current_price)

#     if not holding_entry:
#          raise HTTPException(status_code=500, detail="Failed to update holding")

#     # Recalculate PNL/Value for response if schema expects it
#     pnl = (current_price - holding_entry.average_cost) * holding_entry.shares
#     total_value = current_price * holding_entry.shares

#     # Create response data, potentially mapping to HoldingResponse schema structure
#     response_data = {
#         "shares": holding_entry.shares,
#         # Note: HoldingResponse schema only had shares, total_pnl, total_value.
#         # You might need to add average_cost to the schema if you want to return it.
#         "total_pnl": round(pnl, 2),
#         "total_value": round(total_value, 2),
#     }

#     # Pydantic v2: Use HoldingResponse(**response_data) or return dictionary if schema matches
#     # Assuming HoldingResponse matches the structure above for pnl/total_value
#     return HoldingResponse(**response_data)


# @router.delete("/watchlist/{watchlist_id}")
# async def remove_from_watchlist(...): # This seems less specific than deleting by symbol/id combo.
# Keeping the delete_symbol_from_watchlist endpoint as it seems more precise.
# The delete_watchlist_with_holdings endpoint below also handles deleting a full watchlist entry.
# Keep this if it has a specific use case, otherwise remove for clarity.
# For now, removing the implementation as delete_watchlist_and_holding is implemented below and seems preferred.
# async def remove_from_watchlist(
#     watchlist_id: UUID,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     # Need to verify ownership
#     watchlist_entry = await get_watchlist_by_id(db, watchlist_id)
#     if not watchlist_entry or str(watchlist_entry.user_id) != str(user.id):
#          raise HTTPException(status_code=404, detail="Watchlist not found or does not belong to user")

#     # Call the CRUD function to delete the watchlist entry (without holdings)
#     success = await delete_watchlist(db, watchlist_id) # This CRUD deletes ONLY the watchlist entry
#     if not success:
#          raise HTTPException(status_code=404, detail="Watchlist not found") # Should be caught by the check above, but good fallback
#     return {"detail": f"Watchlist entry ID {watchlist_id} deleted successfully"}


@router.delete("/watchlist/{watchlist_id}/{symbol}")
async def remove_symbol_from_watchlist(
    watchlist_id: UUID,
    symbol: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Deletes a specific symbol entry from a specific watchlist for the user.
    Also deletes the associated holding.
    """
    # The CRUD function already handles ownership verification and deletion of holding
    return await delete_symbol_from_watchlist(db, watchlist_id, user.id, symbol)


@router.get(
    "/watchlist/symbols", response_model=List[Dict[str, Any]]
)  # Adjust response model if you create a specific Pydantic schema for this output
async def get_user_watchlist(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieves all watchlist items for the user with their current data.
    Uses batched yfinance fetching and caching.
    """
    # Use the new batched fetcher which returns combined DB + live data
    watchlist_data_list = await fetch_watchlist_display_data_batched(db, user.id)

    # The fetch_watchlist_display_data_batched already returns the desired dictionary format
    return watchlist_data_list

    # --- Original inefficient loop ---
    # watchlists =  await get_user_watchlist_symbols_crud(db, user.id)
    # watchlist_data = []
    # for watchlist in watchlists:
    #     # This was calling get_stock_data_with_watchid repeatedly inside a loop
    #     # Replacing this with the single call to fetch_watchlist_display_data_batched above
    #     current_data = await get_stock_data_with_watchid(f"{watchlist.symbol}",watchlist.type,watchlist.id)
    #     watchlist_data.append(current_data)
    # return watchlist_data
    # ----------------------------------


@router.get("/watchlistid", response_model=UUID | None)  # Adjust response model
async def get_user_watchlist_id(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieves a watchlist ID for the user. Note: assumes one main watchlist per user.
    """
    watchlist_id = await get_user_watchlist_id_crud(db, user.id)
    if not watchlist_id:
        # Returning 404 seems appropriate if the concept of a single watchlist ID is core
        # If user simply has no items yet, returning None or empty is also an option depending on frontend expectation.
        # Returning None aligns with the function's signature.
        # raise HTTPException(status_code=404, detail="Watchlist not found for user") # Or raise 404
        return None  # Return None if CRUD returns None
    return watchlist_id


@router.delete("/watchlist/{watchlist_id}")
async def delete_watchlist_with_holdings(
    watchlist_id: UUID,
    user=Depends(get_current_user),  # Add dependency to verify ownership
    db: AsyncSession = Depends(get_session),
):
    """
    Deletes a specific watchlist entry (by its ID) and its associated holding.
    Includes user ownership verification.
    """
    # Verify ownership before attempting deletion
    watchlist_entry = await get_watchlist_by_id(db, watchlist_id)
    if not watchlist_entry or str(watchlist_entry.user_id) != str(user.id):
        raise HTTPException(
            status_code=404,
            detail="Watchlist entry not found or does not belong to user",
        )

    # Call the CRUD function to delete the entry and holding
    success = await delete_watchlist_and_holding(db, watchlist_id)
    # The check above ensures it exists and belongs to user, so success should be True if no DB error
    if not success:
        # This case should ideally not be hit if the ownership check passes and no concurrent deletion happens
        raise HTTPException(
            status_code=500, detail="Failed to delete watchlist entry and holding"
        )

    return {
        "detail": f"Watchlist entry ID {watchlist_id} and its holding deleted successfully"
    }


@router.get(
    "/watchlist/{symbol}/holding", response_model=Dict[str, Any]
)  # Adjust response model
async def get_holding_details(
    symbol: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieves holding details for a specific symbol for the user, including calculated PNL and total value.
    Requires fetching the current price.
    """
    # 1. Get the holding entry from the DB
    holding_entry = await get_holding_by_symbol_crud(db, user.id, symbol)
    if not holding_entry:
        # Returning empty list or 404 depending on expected behavior when no holding exists
        raise HTTPException(status_code=404, detail="Holding not found for this symbol")

    # 2. Get the corresponding watchlist entry to determine type and actual symbol casing
    watchlist_entry = await get_watchlist_by_id(db, holding_entry.watchlist_id)
    # This should almost always exist if holding_entry exists, but add a check
    if not watchlist_entry:
        print(
            f"Warning: Holding {holding_entry.id} found without linked Watchlist {holding_entry.watchlist_id}",
            flush=True,
        )
        # Cannot proceed if watchlist info is missing (needed for type/symbol)
        raise HTTPException(
            status_code=500, detail="Internal error: Watchlist data missing for holding"
        )

    # 3. Get the current price for this symbol using the cached single fetcher
    current_data = await get_stock_data(watchlist_entry.symbol, watchlist_entry.type)
    current_price = current_data.get("price")

    if current_price is None or current_price == 0.0 or current_price == "N/A":
        # Cannot calculate PNL/Value if price is unavailable
        raise HTTPException(
            status_code=500, detail=f"Could not fetch current price for {symbol}"
        )

    # 4. Prepare the response data including calculated PNL and total value
    # Use attributes from the ORM object
    pnl = (current_price - holding_entry.average_cost) * holding_entry.shares
    total_value = current_price * holding_entry.shares

    # Return a dictionary representing the holding details + calculated values
    # You might want to define a Pydantic schema for this combined response
    response_data = {
        "id": holding_entry.id,  # Include Holding ID
        "watchlist_id": holding_entry.watchlist_id,  # Include Watchlist ID
        "shares": holding_entry.shares,
        "average_cost": holding_entry.average_cost,
        # Include current price and calculated values
        "current_price": current_price,
        "pnl": round(pnl, 2),
        "total_value": round(total_value, 2),
        # You might want to include symbol and type from the watchlist for clarity
        "symbol": watchlist_entry.symbol,
        "type": watchlist_entry.type,
    }

    return response_data


# get total value of all the assests not just one symbol
@router.get("/totalvalue", response_model=float)  # Specify response model as float
async def get_total_value_of_all_assets_usd(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Calculates the total value of all user holdings in USD.
    Uses batched price fetching and caching.
    """
    # This calls the refactored CRUD function which handles batching and caching
    return await get_total_value_of_all_assets_crud(db, user.id)


@router.get("/totalvalue-gbp", response_model=float)  # Specify response model as float
async def get_total_value_of_all_assets_gbp(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Calculates the total value of all user holdings in GBP.
    Uses batched price fetching, caching, and exchange rate fetching/caching.
    """
    # This calls the refactored CRUD function which handles batching, caching, and conversion
    return await get_total_value_of_all_assets_crud_gbp(db, user.id)


# from typing import List
# from uuid import UUID
# from fastapi import APIRouter, Depends, HTTPException
# from app.crud.holdings import update_holding
# from app.crud.watchlists import create_watchlist, delete_symbol_from_watchlist, delete_watchlist, delete_watchlist_and_holding, get_current_price, get_current_price_stock, get_holding_by_symbol_crud, get_stock_data, get_stock_data_with_watchid, get_total_value_of_all_assets_crud, get_total_value_of_all_assets_crud_gbp, get_user_watchlist_id_crud, get_watchlist_by_id, get_watchlist_by_symbol
# from app.schemas.holdings import HoldingCreate, HoldingResponse
# from app.schemas.watchlists import WatchlistCreate, WatchlistResponse
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.api.deps import get_current_user, get_session
# from app.crud.watchlists import get_user_watchlist_symbols_crud 

# router = APIRouter()


# @router.post("/watchlist")
# async def add_to_watchlist(
#     watchlist_data: WatchlistCreate,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     await create_watchlist(db, user.id, watchlist_data)
#     return f"symbol {watchlist_data.symbol} has been added to watchlist "


# @router.put("/watchlist/{symbol}/holding")
# async def edit_holding(
#     symbol: str,
#     holding_data: HoldingCreate,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     watchlist = await get_watchlist_by_symbol(db, user.id, symbol)
#     if not watchlist:
#         raise HTTPException(status_code=404, detail="Watchlist not found")
    
#     if watchlist.type == 'stocks':
#         current_price = await get_current_price_stock(f"{watchlist.symbol}")
#     else:
#         current_price = await get_current_price(f"{watchlist.symbol}")
#     holding_data = await update_holding(db, watchlist.id, holding_data,current_price)
#     holding_data_dict = vars(holding_data)
#     pnl = (current_price-holding_data_dict['average_cost'])*holding_data_dict['shares']
#     holding_data_dict['pnl'] =pnl
#     total_value = current_price * holding_data_dict['shares']
#     holding_data_dict['total_value'] = total_value
#     return holding_data


# # @router.put("/watchlist/{watchlist_id}/holding", response_model=HoldingResponse)
# # async def edit_holding(
# #     watchlist_id: UUID,
# #     holding_data: HoldingCreate,
# #     user=Depends(get_current_user),
# #     db: AsyncSession = Depends(get_session),
# # ):
# #     watchlist = get_watchlist_by_id(db,watchlist_id)
# #     if not watchlist:
# #         return HTTPException(status_code=404,detail="Watchlist not found")
# #     return await update_holding(db, watchlist_id, holding_data)


# # @router.delete("/watchlist/{watchlist_id}")
# # async def remove_from_watchlist(
# #     watchlist_id: UUID,
# #     user=Depends(get_current_user),
# #     db: AsyncSession = Depends(get_session),
# # ):
# #     return await delete_watchlist(db, watchlist_id)
# @router.delete("/watchlist/{watchlist_id}/{symbol}")
# async def remove_symbol_from_watchlist(
#     watchlist_id: UUID,
#     symbol: str,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     return await delete_symbol_from_watchlist(db, watchlist_id, user.id, symbol)


# @router.get("/watchlist/symbols")
# async def get_user_watchlist(
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     watchlists =  await get_user_watchlist_symbols_crud(db, user.id)
#     watchlist_data = []
#     for watchlist in watchlists:
#         current_data = await get_stock_data_with_watchid(f"{watchlist.symbol}",watchlist.type,watchlist.id)
#         watchlist_data.append(current_data)
        
#     return watchlist_data
    
#     # holding_data_dict = vars(holdings)
#     # pnl = (current_price - holding_data_dict["average_cost"]) * holding_data_dict[
#     #     "shares"
#     # ]
#     # holding_data_dict["pnl"] = pnl
#     # total_value = current_price * holding_data_dict["shares"]
#     # holding_data_dict["total_value"] = total_value
#     # return holding_data_dict


# @router.get("/watchlistid")
# async def get_user_watchlist_id(
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     watchlist_id =  await get_user_watchlist_id_crud(db, user.id)
#     if not watchlist_id:
#         return HTTPException(status_code=404, detail="Watchlist not found")
#     return watchlist_id

# @router.delete("/watchlist/{watchlist_id}")
# async def delete_watchlist_with_holdings(
#     watchlist_id: UUID,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     success = await delete_watchlist_and_holding(db, watchlist_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Watchlist not found")
#     return {"detail": "Watchlist and its holding deleted successfully"}


# @router.get("/watchlist/{symbol}/holding")
# async def get_holding_details(
#     symbol: str,
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     holdings = await get_holding_by_symbol_crud(db, user.id, symbol)
#     if not holdings:
#         return []
#     watchlist = await get_watchlist_by_id(db, holdings.watchlist_id)
#     if not watchlist:
#         raise HTTPException(status_code=404, detail="Watchlist not found")

#     if watchlist.type == 'stocks':
#         current_price = await get_current_price_stock(f"{watchlist.symbol}")
#     else:
#         current_price = await get_current_price(f"{watchlist.symbol}")
#     holding_data_dict = vars(holdings)
#     pnl = (current_price - holding_data_dict["average_cost"]) * holding_data_dict[
#         "shares"
#     ]
#     holding_data_dict["pnl"] = pnl
#     total_value = current_price * holding_data_dict["shares"]
#     holding_data_dict["total_value"] = total_value
#     return holding_data_dict


# #get total value of all the assests not just one symbol
# @router.get("/totalvalue")
# async def get_total_value_of_all_assets(
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
#     ):
#     return await get_total_value_of_all_assets_crud(db, user.id)

# @router.get("/totalvalue-gbp")
# async def get_total_value_of_all_assets_gbp(
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     return await get_total_value_of_all_assets_crud_gbp(db, user.id)
