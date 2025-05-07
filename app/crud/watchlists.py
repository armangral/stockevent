import requests
import json
from sqlalchemy import Tuple, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Dict, Optional
from uuid import UUID
from fastapi import HTTPException  # Keep HTTPException for raising errors

import yfinance as yf
from app.models.holdings import Holding
from app.models.watchlists import Watchlist
from app.schemas.watchlists import WatchlistCreate
from tenacity import retry, stop_after_attempt, wait_exponential

# Assume app.core.cache is implemented as discussed, with async functions
from app.core.cache import (
    get_cached_data,
    set_cached_data,
    get_cache_key,
    CACHE_EXPIRY_SECONDS_SHORT,
    CACHE_EXPIRY_SECONDS_MEDIUM,
)

# Assuming safe_get_info and fetch_tickers_data_batched helpers are available from crud.crypto
# (It's good practice to define these once in a shared place if used across multiple crud files,
# like a utilities or api_helpers module, but for this example, we'll assume they are imported or defined here)


# Re-defining necessary helpers if not importing from elsewhere
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
def fetch_tickers_data_batched(yf_symbols: List[str]) -> yf.Tickers | None:
    """Fetch data for multiple tickers using yf.Tickers with retries."""
    if not yf_symbols:
        print("Called fetch_tickers_data_batched with empty symbol list.")
        return None
    print(f"Attempting batched fetch for {len(yf_symbols)} symbols using yf.Tickers...")
    try:
        tickers = yf.Tickers(yf_symbols)
        # Accessing info immediately might trigger calls, but it's the intended use
        _ = tickers.tickers  # Accessing this populates the tickers dictionary
        return tickers
    except Exception as e:
        print(f"Error during batched fetch for {yf_symbols}: {e}", flush=True)
        raise  # Re-raise to trigger retry


def safe_get_info(info: dict, key: str, default: Any = "N/A"):
    """Safely get a value from the ticker info dictionary."""
    if not isinstance(info, dict):
        return default
    value = info.get(key, default)
    if value is None or (
        isinstance(value, float) and value != value
    ):  # Check for NaN using value != value
        return default
    return value


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_exchange_rate_cached(
    from_currency: str, to_currency: str
) -> float | None:
    """Fetches exchange rate using yfinance with retries and caching."""
    cache_key = get_cache_key("exchange_rate", from_currency, to_currency)
    cached_rate = await get_cached_data(cache_key)

    if cached_rate is not None:
        # print(f"Returning cached exchange rate for {from_currency} to {to_currency}: {cached_rate}", flush=True)
        return cached_rate

    # Cache miss, fetch from yfinance
    yf_symbol = f"{from_currency.upper()}{to_currency.upper()}=X"  # e.g., USDGBP=X for USD to GBP
    print(f"Attempting to fetch exchange rate for {yf_symbol}...")
    try:
        ticker = yf.Ticker(yf_symbol)
        # Use a very short period and interval to get a recent price
        history = ticker.history(
            period="1d", interval="1m"
        )  # Use short interval for near real-time
        if history.empty:
            # If history is empty, check info for last price (less reliable)
            info = ticker.info
            rate = safe_get_info(info, "regularMarketPrice")
            if rate == "N/A":
                rate = safe_get_info(info, "previousClose")
            if rate == "N/A":
                raise ValueError(
                    f"Could not fetch exchange rate for {yf_symbol} (history empty and info price N/A)"
                )
            rate = float(rate)
        else:
            rate = float(history["Close"].iloc[-1])  # Get the latest closing price

        print(
            f"Fetched exchange rate {from_currency} to {to_currency} ({yf_symbol}): {rate}",
            flush=True,
        )
        # Cache the fetched rate
        await set_cached_data(
            cache_key, rate, CACHE_EXPIRY_SECONDS_MEDIUM
        )  # Cache rate for reasonable time

        return rate

    except Exception as e:
        print(
            f"Failed to fetch exchange rate for {from_currency} to {to_currency} after retries: {e}",
            flush=True,
        )
        raise  # Re-raise to trigger tenacity retry


# --- CRUD Operations (mostly unchanged for DB logic) ---


async def create_watchlist(
    db: AsyncSession, user_id: UUID, watchlist_data: WatchlistCreate
):
    existing_watchlist = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user_id,
            Watchlist.symbol.ilike(watchlist_data.symbol),  # Case-insensitive check
            Watchlist.type == watchlist_data.type,
        )
    )
    if existing_watchlist.scalar():
        raise HTTPException(
            status_code=400,
            detail=f"Symbol '{watchlist_data.symbol}' already in watchlist",
        )

    watchlist = Watchlist(
        **watchlist_data.model_dump(), user_id=user_id
    )  # Use model_dump for Pydantic v2
    db.add(watchlist)
    await db.flush()
    # No need to await db.commit() here if using get_session dep which handles it
    return watchlist


async def get_watchlist_by_id(db: AsyncSession, watchlist_id: UUID) -> Watchlist | None:
    # Changed type hint to UUID based on model definition
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    return (
        result.scalar_one_or_none()
    )  # Use scalar_one_or_none for potential single result


async def delete_watchlist(db: AsyncSession, watchlist_id: UUID) -> bool:
    # Changed type hint to UUID
    # This function seems redundant with delete_watchlist_and_holding, check usage
    # Assuming it's intended to delete the watchlist entry ONLY (maybe not holdings?)
    # The delete_watchlist_and_holding seems more complete based on typical use cases
    # Let's keep delete_watchlist_and_holding and potentially remove this one if unused.
    # For now, implementing based on signature but note potential redundancy.

    # Check if the watchlist exists
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        return False  # Watchlist not found

    # Delete ONLY the watchlist entry
    await db.delete(watchlist)
    await db.commit()  # Commit deletion here if this function is standalone
    return True  # Watchlist deleted


async def get_user_watchlist_symbols_crud(
    db: AsyncSession, user_id: UUID
) -> List[Watchlist]:
    """
    Retrieve the watchlist entries for a given user.
    """
    query = select(Watchlist).where(Watchlist.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_user_watchlist_id_crud(db: AsyncSession, user_id: UUID) -> UUID | None:
    # This seems to assume a user has only one watchlist, which might not be true
    # based on the schema (Watchlist table doesn't enforce a single list per user,
    # just many-to-one symbols per user). Re-evaluate if this is intended.
    # If it's just getting *any* watchlist ID for the user, the first one found is returned.
    query = (
        select(Watchlist.id).where(Watchlist.user_id == user_id).limit(1)
    )  # Limit to 1
    result = await db.execute(query)
    watchlist_id = result.scalar_one_or_none()
    return watchlist_id


async def get_holding_by_symbol_crud(
    db: AsyncSession, user_id: UUID, symbol: str
) -> Holding | None:
    """
    Retrieves the holding entry for a specific symbol within a user's watchlist.
    Assumes a symbol is unique per user across all watchlist entries.
    """
    # Note: If a user can have the same symbol in multiple watchlist entries (which the schema allows if not constrained),
    # this query might return multiple holdings if the symbol is in multiple lists.
    # Assuming for now that symbol is intended to be unique per user.
    query = (
        select(Holding)
        .join(Watchlist, Holding.watchlist_id == Watchlist.id)
        .where(
            Watchlist.user_id == user_id, Watchlist.symbol.ilike(symbol)
        )  # Case-insensitive symbol match
        .limit(1)  # Assume unique per user, get the first one
    )
    result = await db.execute(query)
    holding = result.scalar_one_or_none()
    return holding


async def delete_symbol_from_watchlist(
    db: AsyncSession, watchlist_id: UUID, user_id: UUID, symbol: str
):
    """
    Deletes a specific symbol entry from a specific watchlist for a user.
    Also deletes the associated holding if it exists.
    """
    # Check if the watchlist entry exists and belongs to the user
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user_id,
            Watchlist.symbol.ilike(symbol),  # Case-insensitive match
        )
    )
    watchlist_entry = result.scalar_one_or_none()

    if not watchlist_entry:
        raise HTTPException(
            status_code=404,
            detail="Watchlist entry not found or does not belong to user",
        )

    # Get the associated Holding (if any)
    holding_result = await db.execute(
        select(Holding).where(Holding.watchlist_id == watchlist_entry.id)
    )
    holding_entry = holding_result.scalar_one_or_none()

    # Delete the associated Holding
    if holding_entry:
        await db.delete(holding_entry)

    # Delete the Watchlist entry
    await db.delete(watchlist_entry)

    # Commit both deletions
    await db.commit()

    return {"message": f"Symbol '{symbol}' removed from watchlist (ID: {watchlist_id})"}


async def get_watchlist_by_symbol(
    db: AsyncSession, user_id: UUID, symbol: str
) -> Watchlist | None:
    """
    Retrieves a watchlist entry for a specific symbol for a user.
    Assumes symbol is unique per user across all watchlist entries.
    """
    query = (
        select(Watchlist)
        .where(
            Watchlist.user_id == user_id,
            Watchlist.symbol.ilike(symbol),  # Case-insensitive match
        )
        .limit(1)
    )  # Assume unique per user
    result = await db.execute(query)
    return result.scalar_one_or_none()


# --- New Function for Batched Watchlist Display Data Fetching ---


async def fetch_watchlist_display_data_batched(
    db: AsyncSession, user_id: UUID
) -> List[Dict[str, Any]]:
    """
    Fetches all watchlist items for a user and retrieves their current data
    (price, market cap, volume, etc.) using yfinance batching and caching.
    Combines watchlist entry info with live data.
    """
    # 1. Get all watchlist entries for the user
    watchlist_entries = await get_user_watchlist_symbols_crud(db, user_id)

    if not watchlist_entries:
        return []  # User has no watchlist items

    results = []  # List to store final results (cached + fetched + DB info)
    symbols_to_fetch_stock = []  # List of (symbol, watch_id) for stocks not in cache
    symbols_to_fetch_crypto = []  # List of (symbol, watch_id) for crypto not in cache

    # 2. Check cache for each watchlist item
    for entry in watchlist_entries:
        # Create a unique cache key for each specific watchlist item instance
        # Cache key includes watchlist ID and type
        cache_key = get_cache_key("watchlist_item_data", str(entry.id), entry.type)
        cached_item_data = await get_cached_data(cache_key)

        if cached_item_data:
            # Cached data found, add to results
            results.append(cached_item_data)
        else:
            # Not in cache, mark for fetching
            if entry.type.lower() == "stocks":
                symbols_to_fetch_stock.append((entry.symbol, entry.id))
            elif entry.type.lower() == "crypto":
                symbols_to_fetch_crypto.append((entry.symbol, entry.id))
            # Add a placeholder to results to maintain order and link back to DB entry
            results.append(
                {
                    "watch_id": str(entry.id),
                    "symbol": entry.symbol.upper(),
                    "type": entry.type,
                    "price": "N/A",
                    "market_cap": "N/A",
                    "volume_24h": "N/A",
                    # Add placeholder key to find this item later
                    "_cache_key_placeholder": cache_key,
                }
            )

    if not symbols_to_fetch_stock and not symbols_to_fetch_crypto:
        return results  # All data was in cache

    # 3. Fetch data for symbols not found in cache using batching
    fetched_data_map = {}  # Map (original symbol, watch_id) -> fetched data dict

    # Fetch Stock Data
    if symbols_to_fetch_stock:
        stock_yf_symbols = [sym for sym, _ in symbols_to_fetch_stock]
        try:
            stock_tickers_data = fetch_tickers_data_batched(stock_yf_symbols)
            if stock_tickers_data:
                for symbol, watch_id in symbols_to_fetch_stock:
                    ticker_obj = stock_tickers_data.tickers.get(symbol)
                    if ticker_obj:
                        try:
                            info = ticker_obj.info
                            # Fetch price, market cap, volume
                            price = safe_get_info(info, "regularMarketPrice")
                            if price == "N/A":
                                price = safe_get_info(info, "previousClose")

                            market_cap = safe_get_info(info, "marketCap")
                            # Volume can be from info or history - info.volume or history.iloc[-1]['Volume']
                            # Let's get volume from info first
                            volume = safe_get_info(info, "volume")
                            if volume == "N/A":
                                # Fallback to history if necessary (might be slower)
                                history = ticker_obj.history(period="1d")
                                volume = (
                                    safe_get_info(history.iloc[-1], "Volume")
                                    if not history.empty
                                    else "N/A"
                                )

                            fetched_data_map[(symbol, watch_id)] = {
                                "price": price,
                                "market_cap": market_cap,
                                "volume_24h": volume,
                            }
                        except Exception as e:
                            print(
                                f"Error processing fetched stock info for {symbol} (Watchlist ID {watch_id}): {e}",
                                flush=True,
                            )
        except Exception as e:
            print(
                f"Error during batch fetch for stock symbols {stock_yf_symbols}: {e}",
                flush=True,
            )

    # Fetch Crypto Data
    if symbols_to_fetch_crypto:
        crypto_yf_symbols = [f"{sym}-USD" for sym, _ in symbols_to_fetch_crypto]
        try:
            crypto_tickers_data = fetch_tickers_data_batched(crypto_yf_symbols)
            if crypto_tickers_data:
                for symbol, watch_id in symbols_to_fetch_crypto:
                    yf_symbol = f"{symbol}-USD"
                    ticker_obj = crypto_tickers_data.tickers.get(yf_symbol)
                    if ticker_obj:
                        try:
                            info = ticker_obj.info
                            price = safe_get_info(info, "regularMarketPrice")
                            if price == "N/A":
                                price = safe_get_info(info, "previousClose")

                            market_cap = safe_get_info(info, "marketCap")
                            # Crypto volume might be different, use info if available
                            volume = safe_get_info(
                                info, "volume"
                            )  # Check if yfinance provides this for crypto
                            if volume == "N/A":
                                # Fallback to history if necessary
                                history = ticker_obj.history(
                                    period="1d", interval="1h"
                                )  # Use appropriate interval
                                volume = (
                                    safe_get_info(history.iloc[-1], "Volume")
                                    if not history.empty
                                    else "N/A"
                                )

                            fetched_data_map[(symbol, watch_id)] = {
                                "price": price,
                                "market_cap": market_cap,
                                "volume_24h": volume,
                            }
                        except Exception as e:
                            print(
                                f"Error processing fetched crypto info for {symbol} (Watchlist ID {watch_id}): {e}",
                                flush=True,
                            )

        except Exception as e:
            print(
                f"Error during batch fetch for crypto symbols {crypto_yf_symbols}: {e}",
                flush=True,
            )

    # 4. Update placeholders in results list with fetched data and cache newly fetched items
    final_results = []
    for item in results:
        if "_cache_key_placeholder" in item:
            symbol = item[
                "symbol"
            ].lower()  # Use lower case for consistent map key lookup
            watch_id = UUID(item["watch_id"])  # Convert back to UUID for map key

            fetched_item_data = fetched_data_map.get((symbol, watch_id))

            if fetched_item_data:
                # Successfully fetched data, update item and cache
                updated_item = {
                    "watch_id": item["watch_id"],
                    "symbol": item[
                        "symbol"
                    ],  # Keep original casing or standardize? Let's keep original from placeholder
                    "type": item["type"],
                    "price": round(fetched_item_data["price"], 2)
                    if isinstance(fetched_item_data["price"], (int, float))
                    else "N/A",
                    "market_cap": round(fetched_item_data["market_cap"])
                    if isinstance(fetched_item_data["market_cap"], (int, float))
                    else "N/A",
                    "volume_24h": round(fetched_item_data["volume_24h"])
                    if isinstance(fetched_item_data["volume_24h"], (int, float))
                    else "N/A",
                }
                final_results.append(updated_item)
                # Cache the updated item using the placeholder's cache key
                await set_cached_data(
                    item["_cache_key_placeholder"],
                    updated_item,
                    CACHE_EXPIRY_SECONDS_SHORT,
                )
            else:
                # Data not in cache and not successfully fetched, keep placeholder N/A values
                final_results.append(
                    {
                        "watch_id": item["watch_id"],
                        "symbol": item["symbol"],
                        "type": item["type"],
                        "price": "N/A",
                        "market_cap": "N/A",
                        "volume_24h": "N/A",
                    }
                )
        else:
            # This item was from the cache initially, just add it to final results
            final_results.append(item)

    return final_results


# --- Refactor Total Value Calculation to Use Batched Price Fetching ---


# Helper to fetch batched current prices for a list of (symbol, type)
async def fetch_current_prices_for_total_value(
    items: List[Tuple[str, str]],  # List of (symbol, type) tuples
) -> Dict[Tuple[str, str], float]:
    """
    Fetches current prices for a list of (symbol, type) pairs using batching and caching.
    Returns a dictionary mapping (symbol, type) -> price.
    """
    if not items:
        return {}

    # Create unique list of (symbol, type) pairs
    unique_items = list(set(items))

    prices_map = {}  # Map (symbol, type) -> price
    symbols_to_fetch_stock = []  # List of symbol for stocks not in cache
    symbols_to_fetch_crypto = []  # List of symbol for crypto not in cache

    # 1. Check cache for each item
    for symbol, item_type in unique_items:
        # Use a cache key specific for current price in total value context, including type
        cache_key = get_cache_key("current_price", symbol, item_type)
        cached_price = await get_cached_data(cache_key)

        if cached_price is not None:
            prices_map[(symbol, item_type)] = cached_price
        else:
            if item_type.lower() == "stocks":
                symbols_to_fetch_stock.append(symbol)
            elif item_type.lower() == "crypto":
                symbols_to_fetch_crypto.append(symbol)

    # 2. Fetch data for symbols not found in cache using batching
    fetched_prices_map = {}  # Map yf_symbol -> price

    if symbols_to_fetch_stock:
        try:
            stock_tickers_data = fetch_tickers_data_batched(symbols_to_fetch_stock)
            if stock_tickers_data:
                for symbol in symbols_to_fetch_stock:
                    ticker_obj = stock_tickers_data.tickers.get(symbol)
                    if ticker_obj:
                        try:
                            info = ticker_obj.info
                            price = safe_get_info(info, "regularMarketPrice")
                            if price == "N/A":
                                price = safe_get_info(info, "previousClose")
                            if price != "N/A":
                                fetched_prices_map[symbol] = float(price)
                        except Exception as e:
                            print(
                                f"Error processing fetched stock price for {symbol}: {e}",
                                flush=True,
                            )
        except Exception as e:
            print(
                f"Error during batch fetch for stock prices {symbols_to_fetch_stock}: {e}",
                flush=True,
            )

    if symbols_to_fetch_crypto:
        crypto_yf_symbols = [f"{sym}-USD" for sym in symbols_to_fetch_crypto]
        try:
            crypto_tickers_data = fetch_tickers_data_batched(crypto_yf_symbols)
            if crypto_tickers_data:
                for symbol in symbols_to_fetch_crypto:
                    yf_symbol = f"{symbol}-USD"
                    ticker_obj = crypto_tickers_data.tickers.get(yf_symbol)
                    if ticker_obj:
                        try:
                            info = ticker_obj.info
                            price = safe_get_info(info, "regularMarketPrice")
                            if price == "N/A":
                                price = safe_get_info(info, "previousClose")
                            if price != "N/A":
                                fetched_prices_map[yf_symbol] = float(price)
                        except Exception as e:
                            print(
                                f"Error processing fetched crypto price for {symbol}: {e}",
                                flush=True,
                            )
        except Exception as e:
            print(
                f"Error during batch fetch for crypto prices {crypto_yf_symbols}: {e}",
                flush=True,
            )

    # 3. Update prices map with fetched data and cache
    for symbol, item_type in unique_items:
        if (symbol, item_type) not in prices_map:  # Check if it was already cached
            yf_symbol = f"{symbol}-USD" if item_type.lower() == "crypto" else symbol
            price = fetched_prices_map.get(
                yf_symbol
            )  # Get from fetched map using yfinance symbol if crypto

            if price is not None:
                prices_map[(symbol, item_type)] = price
                # Cache the fetched price
                cache_key = get_cache_key("current_price", symbol, item_type)
                await set_cached_data(cache_key, price, CACHE_EXPIRY_SECONDS_SHORT)
            else:
                # Price not found in cache or fetched
                prices_map[(symbol, item_type)] = (
                    0.0  # Default to 0.0 if price couldn't be retrieved
                )

    return prices_map


async def get_total_value_of_all_assets_crud(db: AsyncSession, user_id: UUID) -> float:
    """
    Calculates the total value of all assets in the user's holdings (USD) using batched price fetching.
    """
    # Fetch all symbols, types, and shares from holdings
    result = await db.execute(
        select(Watchlist.symbol, Watchlist.type, Holding.shares)
        .join(Watchlist, Holding.watchlist_id == Watchlist.id)
        .where(Watchlist.user_id == user_id)
    )
    holdings_data = result.all()  # List of (symbol, type, shares)

    if not holdings_data:
        return 0.0  # No holdings, total value is 0

    # Collect unique (symbol, type) pairs to fetch prices
    items_to_price = list(
        {(symbol, item_type) for symbol, item_type, shares in holdings_data}
    )

    # Fetch current prices for all unique items in a batch
    prices_map = await fetch_current_prices_for_total_value(items_to_price)

    total_value = 0.0
    # Calculate total value using fetched prices
    for symbol, item_type, shares in holdings_data:
        price = prices_map.get(
            (symbol, item_type), 0.0
        )  # Get price, default to 0.0 if missing
        if isinstance(price, (int, float)):
            total_value += shares * price
        else:
            # Log a warning if price is N/A unexpectedly, but continue calculation
            print(
                f"Warning: Price for {symbol} ({item_type}) is {price}, cannot calculate value for {shares} shares.",
                flush=True,
            )

    return total_value


async def get_total_value_of_all_assets_crud_gbp(
    db: AsyncSession, user_id: UUID
) -> float:
    """
    Calculates the total value of all assets in the user's holdings (GBP) using batched price fetching.
    """
    # Fetch all symbols, types, and shares from holdings (same as USD version)
    result = await db.execute(
        select(Watchlist.symbol, Watchlist.type, Holding.shares)
        .join(Watchlist, Holding.watchlist_id == Watchlist.id)
        .where(Watchlist.user_id == user_id)
    )
    holdings_data = result.all()  # List of (symbol, type, shares)

    if not holdings_data:
        return 0.0  # No holdings, total value is 0

    # 1. Fetch USD to GBP conversion rate once with retries and cache
    usd_to_gbp_rate = await fetch_exchange_rate_cached("USD", "GBP")
    if usd_to_gbp_rate is None:
        print(
            "USD to GBP rate not available, cannot calculate total value in GBP.",
            flush=True,
        )
        return 0.0  # Cannot convert if rate is missing

    # 2. Collect unique (symbol, type) pairs to fetch prices (in USD)
    items_to_price_usd = list(
        {(symbol, item_type) for symbol, item_type, shares in holdings_data}
    )

    # 3. Fetch current prices for all unique items in a batch (in USD)
    prices_map_usd = await fetch_current_prices_for_total_value(
        items_to_price_usd
    )  # This function fetches USD prices

    total_value_usd = 0.0
    # 4. Calculate total value in USD using fetched prices
    for symbol, item_type, shares in holdings_data:
        price_usd = prices_map_usd.get(
            (symbol, item_type), 0.0
        )  # Get USD price, default to 0.0 if missing
        if isinstance(price_usd, (int, float)):
            total_value_usd += shares * price_usd
        else:
            print(
                f"Warning: USD Price for {symbol} ({item_type}) is {price_usd}, cannot calculate value for {shares} shares.",
                flush=True,
            )

    # 5. Convert total USD value to GBP
    total_value_gbp = total_value_usd * usd_to_gbp_rate

    return total_value_gbp


# --- Refactor Single Price/Data Functions ---
# These are less critical for batching but should use caching and retries if used.


async def get_stock_data(symbol: str, item_type: str) -> dict:
    """
    Fetches the current price, market cap, and 24-hour volume of a single symbol using yfinance and caching.
    Used for single lookups, not recommended for lists.
    """
    symbol = symbol.upper()
    item_type = item_type.lower()
    yf_symbol = f"{symbol}-USD" if item_type == "crypto" else symbol

    # 1. Check cache
    cache_key = get_cache_key("single_item_data", symbol, item_type)
    cached_data = await get_cached_data(cache_key)

    if cached_data:
        print(
            f"Returning cached single item data for {symbol} ({item_type})", flush=True
        )
        return cached_data

    # 2. Cache miss, fetch from yfinance (single ticker fetch with retries)
    try:
        # Using yf.Ticker directly here, wrapped in retry, for single fetch efficiency
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=1, min=4, max=30),
        )
        def fetch_single_ticker_data(symbol_to_fetch):
            print(f"Attempting single fetch for {symbol_to_fetch}...")
            ticker = yf.Ticker(symbol_to_fetch)
            # Fetch history for volume, info for other data
            history = ticker.history(period="1d")
            info = ticker.info
            if not history.empty and info:
                return history.iloc[-1], info
            elif info:
                # Return info even if history is empty
                return None, info
            else:
                raise ValueError(
                    f"Could not fetch info or history for {symbol_to_fetch}"
                )  # Trigger retry

        history_last_row, info = fetch_single_ticker_data(yf_symbol)

        # Process data
        price = safe_get_info(info, "regularMarketPrice")
        if price == "N/A" and history_last_row is not None:
            price = safe_get_info(history_last_row, "Close")
        if price == "N/A":
            price = safe_get_info(info, "previousClose")  # Final fallback

        market_cap = safe_get_info(info, "marketCap")
        volume = safe_get_info(info, "volume")  # From info first
        if volume == "N/A" and history_last_row is not None:
            volume = safe_get_info(history_last_row, "Volume")  # Fallback to history

        result_data = {
            "symbol": symbol,
            "type": item_type,
            "price": float(price) if isinstance(price, (int, float)) else 0.0,
            "market_cap": float(market_cap)
            if isinstance(market_cap, (int, float))
            else 0.0,
            "volume_24h": float(volume) if isinstance(volume, (int, float)) else 0.0,
        }

        # 3. Cache the fetched data
        await set_cached_data(
            cache_key, result_data, CACHE_EXPIRY_SECONDS_MEDIUM
        )  # Cache single item for slightly longer

        return result_data

    except Exception as e:
        print(
            f"Error fetching single data for {yf_symbol} after retries: {e}", flush=True
        )
        # Return default N/A data on failure
        return {
            "symbol": symbol,
            "type": item_type,
            "price": 0.0,
            "market_cap": 0.0,
            "volume_24h": 0.0,
        }


# Removed get_stock_data_with_watchid as it seems redundant if fetch_watchlist_display_data_batched is used for lists.
# If you need single lookups including watch_id elsewhere, add caching/retries to it similarly to get_stock_data.


# Removed get_current_price and get_current_price_stock
# Their functionality is now handled by the batched price fetcher (fetch_current_prices_for_total_value)
# or the single item fetcher (get_stock_data) when needed.

# Removed get_usd_to_gbp_rate as fetch_exchange_rate_cached replaces it.


async def delete_watchlist_and_holding(db: AsyncSession, watchlist_id: UUID) -> bool:
    # Fetch the watchlist
    result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
    watchlist = result.scalar_one_or_none()

    if not watchlist:
        return False

    # First delete the associated Holding (if any)
    await db.execute(delete(Holding).where(Holding.watchlist_id == watchlist_id))

    # Then delete the Watchlist
    await db.delete(watchlist)

    await db.commit()
    return True


# from typing import Any, List
# from uuid import UUID
# from fastapi import HTTPException
# import requests
# from sqlalchemy import Tuple, delete, func, select
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.models.holdings import Holding
# from app.models.watchlists import Watchlist
# from app.schemas.holdings import HoldingResponse
# from app.schemas.watchlists import WatchlistCreate
# import yfinance as yf


# # CRUD Operations
# async def create_watchlist(db: AsyncSession,user_id:UUID, watchlist_data: WatchlistCreate):
#     existing_watchlist = await db.execute(
#         select(Watchlist).where(
#             Watchlist.user_id == user_id,
#             Watchlist.symbol == watchlist_data.symbol,
#             Watchlist.type == watchlist_data.type
#         )
#     )
#     if existing_watchlist.scalar():
#         raise HTTPException(status_code=400, detail="Symbol already in watchlist")

#     watchlist = Watchlist(**watchlist_data.dict(),user_id = user_id)
#     db.add(watchlist)
#     await db.flush()
#     return watchlist




# async def get_watchlist_by_id(db: AsyncSession, watchlist_id: int) -> Watchlist | None:
#     result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
#     return result.scalar()


# async def delete_watchlist(db: AsyncSession, watchlist_id: int):
#     result = await db.execute(select(Watchlist).filter(Watchlist.id == watchlist_id))
#     watchlist = result.scalar()
#     if watchlist:
#         await db.execute(delete(Watchlist).where(Watchlist.id == watchlist_id))
#         await db.commit()
#     return watchlist


# # async def get_user_watchlist_symbols_crud(
# #     db: AsyncSession, user_id: UUID
# # ):
# #     query = select(Watchlist).where(Watchlist.user_id == user_id)
# #     result = await db.execute(query)
# #     return result.scalars().all()


# async def get_user_watchlist_symbols_crud(
#     db: AsyncSession, user_id: UUID
# ) -> List[Watchlist]:
#     """
#     Retrieve the watchlist symbols for a given user.

#     Args:
#         db (AsyncSession): Database session.
#         user_id (UUID): The ID of the user.

#     Returns:
#         List[Watchlist]: A list of watchlist entries for the user.
#     """

#     query = select(Watchlist).where(Watchlist.user_id == user_id)
#     result = await db.execute(query)
#     return result.scalars().all()



# # async def get_user_watchlist_symbols_crud(db: AsyncSession, user_id: UUID) -> List[str]:
# #     query = select(Watchlist.symbol).where(Watchlist.user_id == user_id)
# #     result = await db.execute(query)
# #     return [row[0] for row in result.fetchall()]

# async def get_user_watchlist_id_crud(db: AsyncSession, user_id: UUID) -> UUID | None:
#     query = select(Watchlist.id).where(Watchlist.user_id == user_id)
#     result = await db.execute(query)
#     watchlist_id = result.scalar_one_or_none()  # Fetch only one result or None
#     return watchlist_id


# async def get_holding_by_symbol_crud(
#     db: AsyncSession, user_id: UUID, symbol: str
# ):
#     query = (
#         select(Holding)
#         .join(Watchlist, Holding.watchlist_id == Watchlist.id)
#         .where(Watchlist.user_id == user_id, Watchlist.symbol == symbol)
#     )
#     result = await db.execute(query)
#     holding = result.scalar_one_or_none()
#     if not holding:
#         return None
#     return holding


# async def delete_symbol_from_watchlist(
#     db: AsyncSession, watchlist_id: UUID, user_id: UUID, symbol: str
# ):
#     # Check if the watchlist exists and belongs to the user
#     result = await db.execute(
#         select(Watchlist).where(
#             Watchlist.id == watchlist_id, Watchlist.user_id == user_id
#         )
#     )
#     watchlist = result.scalar_one_or_none()

#     if not watchlist:
#         raise HTTPException(
#             status_code=404, detail="Watchlist not found or does not belong to user"
#         )

#     # Find and delete the symbol from this watchlist
#     delete_query = delete(Watchlist).where(
#         Watchlist.id == watchlist_id, Watchlist.symbol == symbol
#     )
#     result = await db.execute(delete_query)

#     if result.rowcount == 0:  # If no rows were deleted, the symbol was not found
#         raise HTTPException(status_code=404, detail="Symbol not found in watchlist")

#     await db.commit()
#     return {"message": f"Symbol '{symbol}' removed from watchlist"}

# async def get_watchlist_by_symbol(db: AsyncSession, user_id: UUID, symbol: str):
#     result = await db.execute(
#         select(Watchlist).where(
#             Watchlist.user_id == user_id, Watchlist.symbol == symbol
#         )
#     )
#     return result.scalar_one_or_none()

# async def get_total_value_of_all_assets_crud(db: AsyncSession, user_id: UUID):
#     # Fetch all symbols and their respective holdings
#     result = await db.execute(
#         select(Watchlist.symbol, Watchlist.type, Holding.shares)
#         .join(Watchlist, Holding.watchlist_id == Watchlist.id)
#         .where(Watchlist.user_id == user_id)
#     )

#     holdings = result.all()

#     total_value = 0.0
#     for symbol, type, shares in holdings:
        
#         print("type is",type)
#         print("shares are ",shares)
#         if type == 'stock':
#             current_price = await get_current_price_stock(symbol)  # Fetch live price
#             print(f"current_price ",current_price)
#             total_value += shares * current_price  # Compute total value
#             print("total_value ",total_value)
#         else:
#             current_price = await get_current_price(symbol)  # Fetch live price
#             total_value += shares * current_price  # Compute total value

#     return total_value


# import yfinance as yf


# async def get_stock_data(symbol: str, type: str) -> dict:
#     """
#     Fetches the current price, market cap, and 24-hour volume of a given stock symbol using yfinance.
#     """
#     try:
#         if type == "stocks":
#             print("type is stock")
#             stock = yf.Ticker(symbol)
#         else:
#             stock = yf.Ticker(f"{symbol}-USD")

#         history = stock.history(period="1d")
#         price = (
#             history["Close"].iloc[-1]
#             if not history.empty
#             else stock.info.get("previousClose", 0.0)
#         )

#         info = stock.info
#         market_cap = info.get("marketCap", 0.0)
#         volume = (
#             history["Volume"].iloc[-1]
#             if not history.empty
#             else info.get("volume", info.get("averageVolume", 0.0))
#         )

#         return {
#             "symbol": symbol.upper(),
#             "type": type,
#             "price": float(price),
#             "market_cap": float(market_cap),
#             "volume_24h": float(volume),
#         }

#     except Exception as e:
#         print(f"Error fetching data for {symbol}: {e}")
#         return {
#             "symbol": symbol.upper(),
#             "type": type,
#             "price": 0.0,
#             "market_cap": 0.0,
#             "volume_24h": 0.0,
#         }


# async def get_stock_data_with_watchid(symbol: str, type: str,watch_id: UUID) -> dict:
#     """
#     Fetches the current price, market cap, and 24-hour volume of a given stock symbol using yfinance.
#     """
#     try:
#         if type == "stocks":
#             print("type is stock")
#             stock = yf.Ticker(symbol)
#         else:
#             stock = yf.Ticker(f"{symbol}-USD")

#         history = stock.history(period="1d")
#         price = (
#             history["Close"].iloc[-1]
#             if not history.empty
#             else stock.info.get("previousClose", 0.0)
#         )

#         info = stock.info
#         market_cap = info.get("marketCap", 0.0)
#         volume = (
#             history["Volume"].iloc[-1]
#             if not history.empty
#             else info.get("volume", info.get("averageVolume", 0.0))
#         )

#         return {
#             "watch_id": watch_id,
#             "symbol": symbol.upper(),
#             "type": type,
#             "price": float(price),
#             "market_cap": float(market_cap),
#             "volume_24h": float(volume),
#         }

#     except Exception as e:
#         print(f"Error fetching data for {symbol}: {e}")
#         return {
#             "symbol": symbol.upper(),
#             "type": type,
#             "price": 0.0,
#             "market_cap": 0.0,
#             "volume_24h": 0.0,
#         }


# # async def get_stock_data(symbol: str,type:str) -> dict:
# #     """
# #     Fetches the current price, market cap, and 24-hour volume of a given stock symbol using yfinance.

# #     :param symbol: Stock symbol (e.g., "AAPL", "TSLA").
# #     :return: Dictionary with price, market cap, and 24-hour volume.
# #     """
# #     try:
# #         if type == 'stocks':
# #             print("type is stock")
# #             stock = yf.Ticker(f"{symbol}")
# #         else:
# #             stock = yf.Ticker(f"{symbol}-USD")
# #         history = stock.history(period="1d")
# #         price = history["Close"].iloc[-1] if not history.empty else 0.0

# #         info = stock.info
# #         market_cap = info.get("marketCap", 0.0)
# #         volume = history["Volume"].iloc[-1] if not history.empty else 0.0

# #         return {
# #             "symbol": symbol.upper(),
# #             "type": type,
# #             "price": float(price),
# #             "market_cap": float(market_cap),
# #             "volume_24h": float(volume),
# #         }
# #     except Exception as e:
# #         print(f"Error fetching data for {symbol}: {e}")
# #         return {
# #             "symbol": symbol.upper(),
# #             "type": type,
# #             "price": 0.0,
# #             "market_cap": 0.0,
# #             "volume_24h": 0.0,
# #         }


# async def get_current_price(symbol: str) -> float:
#     """
#     Fetches the current price of a given stock symbol using yfinance.

#     :param symbol: Stock symbol (e.g., "AAPL", "TSLA").
#     :return: Current price as a float.
#     """
#     try:
#         stock = yf.Ticker(f"{symbol}-usd")
#         price = stock.history(period="1d")["Close"].iloc[
#             -1
#         ]  # Get the latest closing price
#         return float(price)
#     except Exception as e:
#         print(f"Error fetching price for {symbol}: {e}")
#         return 0.0  # Default to 0.0 in case of an error
    
# async def get_current_price_stock(symbol: str) -> float:
#     """
#     Fetches the current price of a given stock symbol using yfinance.

#     :param symbol: Stock symbol (e.g., "AAPL", "TSLA").
#     :return: Current price as a float.
#     """
#     try:
#         stock = yf.Ticker(f"{symbol}")
#         price = stock.history(period="1d")["Close"].iloc[
#             -1
#         ]  # Get the latest closing price
#         return float(price)
#     except Exception as e:
#         print(f"Error fetching price for {symbol}: {e}")
#         return 0.0  # Default to 0.0 in case of an error


# async def get_usd_to_gbp_rate():
#     # Example API call to fetch USD to GBP conversion rate
#     response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
#     data = response.json()
#     return data["rates"]["GBP"]


# async def get_total_value_of_all_assets_crud_gbp(db: AsyncSession, user_id: UUID):
#     # Fetch all symbols and their respective holdings
#     result = await db.execute(
#         select(Watchlist.symbol, Watchlist.type, Holding.shares)
#         .join(Watchlist, Holding.watchlist_id == Watchlist.id)
#         .where(Watchlist.user_id == user_id)
#     )

#     holdings = result.all()

#     total_value_usd = 0.0
#     for symbol, type, shares in holdings:
#         print("type is", type)
#         if type == "stock":
#             current_price = await get_current_price_stock(symbol)  # Fetch live price
#             total_value_usd += shares * current_price  # Compute total value
#         else:
#             current_price = await get_current_price(symbol)  # Fetch live price
#             total_value_usd += shares * current_price  # Compute total value
#         current_price = await get_current_price(symbol)  # Fetch live price


#     # Convert USD to GBP
#     usd_to_gbp_rate = await get_usd_to_gbp_rate()
#     total_value_gbp = total_value_usd * usd_to_gbp_rate

#     return total_value_gbp

# async def delete_watchlist_and_holding(db: AsyncSession, watchlist_id: UUID) -> bool:
#     # Fetch the watchlist
#     result = await db.execute(select(Watchlist).where(Watchlist.id == watchlist_id))
#     watchlist = result.scalar_one_or_none()

#     if not watchlist:
#         return False

#     # First delete the associated Holding (if any)
#     await db.execute(delete(Holding).where(Holding.watchlist_id == watchlist_id))

#     # Then delete the Watchlist
#     await db.delete(watchlist)

#     await db.commit()
#     return True