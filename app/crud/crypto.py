import requests
import json  # Needed for potential manual json handling, though redis-py decodes
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import yfinance as yf
# from forex_python.converter import CurrencyRates # Not used in current code, keep if needed elsewhere

from tenacity import retry, stop_after_attempt, wait_exponential

# Assume app.core.cache is implemented as discussed, with async functions
from app.core.cache import (
    get_cached_data,
    set_cached_data,
    get_cache_key,
    CACHE_EXPIRY_SECONDS_SHORT,
    CACHE_EXPIRY_SECONDS_MEDIUM,
    CACHE_EXPIRY_SECONDS_LONG,
)


# --- Retry Decorators for yfinance calls ---
# Adjust stop and wait parameters based on observed rate limit behavior
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
def fetch_tickers_data_batched(yf_symbols: List[str]) -> yf.Tickers:
    """Fetch data for multiple tickers using yf.Tickers with retries."""
    if not yf_symbols:
        print("Called fetch_tickers_data_batched with empty symbol list.")
        return None  # Or return an empty yf.Tickers object if possible/appropriate
    print(f"Attempting batched fetch for {len(yf_symbols)} symbols...")
    # yf.Tickers might still make multiple requests internally for different data types (info, history, etc.)
    # The key here is that creating *one* Tickers object is better than creating many Ticker objects.
    return yf.Tickers(yf_symbols)


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
def fetch_historical_data_single_ticker(yf_symbol: str, period: str, interval: str):
    """Fetches historical data for a single ticker with retries."""
    print(f"Attempting historical fetch for {yf_symbol} ({period}/{interval})...")
    ticker = yf.Ticker(yf_symbol)
    history = ticker.history(period=period, interval=interval)
    # yfinance history can sometimes return empty even if ticker is valid
    # Don't raise ValueError if empty, just return empty DataFrame
    # if history.empty:
    #      raise ValueError(f"Historical data empty for {yf_symbol} ({period}/{interval})")
    return history


# --- Helper to safely get data from info dict ---
def safe_get_info(info: dict, key: str, default: Any = "N/A"):
    """Safely get a value from the ticker info dictionary."""
    if not isinstance(info, dict):
        return default  # Ensure info is a dictionary

    value = info.get(key, default)
    # Convert None or NaN from yfinance to our default "N/A" if necessary
    if value is None or (
        isinstance(value, float) and value != value
    ):  # Check for NaN using value != value
        return default
    return value


# --- Refactored CRUD Functions ---


async def fetch_crypto_data_crud(
    db: AsyncSession, symbols_info_list: List[Dict], currency: str
):
    """
    Fetches current data for a list of cryptocurrencies using yfinance batching and caching.
    """
    if not symbols_info_list:
        return []

    currency = currency.upper()  # Standardize currency
    results = []  # List to store final results (cached + fetched)
    symbols_to_fetch = []  # List of symbols not found in cache

    # 1. Check cache first for each symbol
    for symbol_info in symbols_info_list:
        symbol = symbol_info["symbol"]
        image = symbol_info["image"]
        cache_key = get_cache_key("crypto_current", symbol, currency)
        cached_item = await get_cached_data(cache_key)

        if cached_item:
            results.append(cached_item)
        else:
            symbols_to_fetch.append(symbol)
            # Add a placeholder to results list now to maintain order and include logo
            results.append(
                {
                    "symbol": symbol,
                    "price": "N/A",
                    "market_cap": "N/A",
                    "change_percent": "N/A",
                    "logo_url": image,
                    "_cache_key_placeholder": cache_key,  # Use a temporary key to find this later
                }
            )

    if not symbols_to_fetch:
        return results  # All data was in cache

    # 2. Fetch data for symbols not found in cache using batching
    yf_symbols_to_fetch = [f"{s}-{currency}" for s in symbols_to_fetch]
    fetched_data_map = {}  # Map original symbol to fetched info/history

    try:
        tickers_data = fetch_tickers_data_batched(yf_symbols_to_fetch)
        if tickers_data:
            # Access info for each ticker within the batched object
            for yf_symbol in yf_symbols_to_fetch:
                original_symbol = yf_symbol.replace(f"-{currency}", "")
                ticker_obj = tickers_data.tickers.get(yf_symbol)
                if ticker_obj:
                    try:
                        # Fetch info and potentially recent history
                        info = ticker_obj.info
                        # Get current price - regularMarketPrice is often available instantly
                        price = safe_get_info(info, "regularMarketPrice")
                        if (
                            price == "N/A"
                        ):  # Fallback to previous close if live price not available
                            price = safe_get_info(info, "previousClose")

                        # You might need history for Open/Close - decide if essential
                        # history = ticker_obj.history(period="1d", interval="1h")
                        # last_close_hist = history["Close"].iloc[-1] if not history.empty else "N/A"
                        # price = price if price != "N/A" else last_close_hist # Prioritize regularMarketPrice

                        fetched_data_map[original_symbol] = {
                            "price": price,
                            "market_cap": safe_get_info(info, "marketCap"),
                            "change_percent": safe_get_info(
                                info, "regularMarketChangePercent"
                            ),
                            # Add any other necessary info from the batch
                        }
                    except Exception as e:
                        print(
                            f"Error processing fetched info for {original_symbol}: {e}",
                            flush=True,
                        )
                        # This symbol will remain N/A in the results
                else:
                    print(f"No ticker object in batch for {yf_symbol}", flush=True)

    except Exception as e:
        print(
            f"Error during batch fetch for crypto symbols {symbols_to_fetch}: {e}",
            flush=True,
        )
        # Error already logged by retry decorator

    # 3. Update placeholders in results list and cache newly fetched data
    final_results = []
    for item in results:
        if "_cache_key_placeholder" in item:
            symbol = item["symbol"]
            original_info = next(
                info for info in symbols_info_list if info["symbol"] == symbol
            )  # Get original info for logo etc.
            image = original_info["image"]

            fetched_item_data = fetched_data_map.get(symbol)

            if fetched_item_data:
                # Successfully fetched data, update item and cache
                updated_item = {
                    "symbol": symbol,
                    "price": round(fetched_item_data["price"], 2)
                    if isinstance(fetched_item_data["price"], (int, float))
                    else "N/A",
                    "market_cap": round(fetched_item_data["market_cap"])
                    if isinstance(fetched_item_data["market_cap"], (int, float))
                    else "N/A",
                    "change_percent": round(
                        fetched_item_data["change_percent"] * 100, 2
                    )
                    if isinstance(fetched_item_data["change_percent"], (int, float))
                    else "N/A",
                    "logo_url": image,
                }
                final_results.append(updated_item)
                # Cache the updated item
                await set_cached_data(
                    item["_cache_key_placeholder"],
                    updated_item,
                    CACHE_EXPIRY_SECONDS_SHORT,
                )
            else:
                # Data not in cache and not successfully fetched, keep placeholder values (or ensure N/A)
                final_results.append(
                    {
                        "symbol": symbol,
                        "price": "N/A",
                        "market_cap": "N/A",
                        "change_percent": "N/A",
                        "logo_url": image,
                    }
                )
        else:
            # This item was from the cache initially, just add it to final results
            final_results.append(item)

    return final_results


async def fetch_stock_data_crud(db: AsyncSession, tickers_info_list: List[Dict]):
    """
    Fetches current data for a list of stocks using yfinance batching and caching.
    """
    if not tickers_info_list:
        return []

    results = []  # List to store final results (cached + fetched)
    symbols_to_fetch = []  # List of symbols not found in cache

    # 1. Check cache first for each symbol
    for ticker_info in tickers_info_list:
        symbol = ticker_info["symbol"]
        cache_key = get_cache_key("stock_current", symbol)
        cached_item = await get_cached_data(cache_key)

        if cached_item:
            results.append(cached_item)
        else:
            symbols_to_fetch.append(symbol)
            # Add a placeholder
            results.append(
                {
                    "symbol": symbol,
                    "price": "N/A",
                    "change_percent": "N/A",
                    "market_cap": "N/A",
                    "sector": "N/A",
                    "industry": ticker_info["company_name"],
                    "logo_url": ticker_info["logo_url"],
                    "_cache_key_placeholder": cache_key,
                }
            )

    if not symbols_to_fetch:
        return results  # All data was in cache

    # 2. Fetch data for symbols not found in cache using batching
    fetched_data_map = {}
    try:
        tickers_data = fetch_tickers_data_batched(symbols_to_fetch)
        if tickers_data:
            for symbol in symbols_to_fetch:
                ticker_obj = tickers_data.tickers.get(symbol)
                if ticker_obj:
                    try:
                        info = ticker_obj.info
                        price = safe_get_info(info, "regularMarketPrice")
                        if price == "N/A":
                            price = safe_get_info(info, "previousClose")

                        fetched_data_map[symbol] = {
                            "price": price,
                            "change_percent": safe_get_info(
                                info, "regularMarketChangePercent"
                            ),
                            "market_cap": safe_get_info(info, "marketCap"),
                            "sector": safe_get_info(info, "sector"),
                        }
                    except Exception as e:
                        print(
                            f"Error processing fetched info for {symbol}: {e}",
                            flush=True,
                        )

    except Exception as e:
        print(
            f"Error during batch fetch for stock symbols {symbols_to_fetch}: {e}",
            flush=True,
        )

    # 3. Update placeholders in results list and cache newly fetched data
    final_results = []
    for item in results:
        if "_cache_key_placeholder" in item:
            symbol = item["symbol"]
            original_info = next(
                info for info in tickers_info_list if info["symbol"] == symbol
            )  # Get original info

            fetched_item_data = fetched_data_map.get(symbol)

            if fetched_item_data:
                updated_item = {
                    "symbol": symbol,
                    "price": round(fetched_item_data["price"], 2)
                    if isinstance(fetched_item_data["price"], (int, float))
                    else "N/A",
                    "change_percent": round(
                        fetched_item_data["change_percent"] * 100, 2
                    )
                    if isinstance(fetched_item_data["change_percent"], (int, float))
                    else "N/A",
                    "market_cap": round(fetched_item_data["market_cap"])
                    if isinstance(fetched_item_data["market_cap"], (int, float))
                    else "N/A",
                    "sector": fetched_item_data["sector"],
                    "industry": original_info["company_name"],
                    "logo_url": original_info["logo_url"],
                }
                final_results.append(updated_item)
                await set_cached_data(
                    item["_cache_key_placeholder"],
                    updated_item,
                    CACHE_EXPIRY_SECONDS_SHORT,
                )
            else:
                final_results.append(
                    {
                        "symbol": symbol,
                        "price": "N/A",
                        "change_percent": "N/A",
                        "market_cap": "N/A",
                        "sector": "N/A",
                        "industry": original_info["company_name"],
                        "logo_url": original_info["logo_url"],
                    }
                )
        else:
            final_results.append(item)

    return final_results


async def fetch_stock_data_crud_with_positions(
    db: AsyncSession, tickers_info_list: List[Dict]
):
    """
    Fetches current data including open/close prices for a list of stocks
    using yfinance batching and caching.
    """
    if not tickers_info_list:
        return []

    results = []  # List to store final results (cached + fetched)
    symbols_to_fetch = []  # List of symbols not found in cache

    # 1. Check cache first for each symbol
    for ticker_info in tickers_info_list:
        symbol = ticker_info["symbol"]
        cache_key = get_cache_key("stock_current_pos", symbol)
        cached_item = await get_cached_data(cache_key)

        if cached_item:
            results.append(cached_item)
        else:
            symbols_to_fetch.append(symbol)
            # Add a placeholder
            results.append(
                {
                    "symbol": symbol,
                    "price": "N/A",
                    "open": "N/A",
                    "close": "N/A",
                    "change_percent": "N/A",
                    "market_cap": "N/A",
                    "sector": "N/A",
                    "industry": ticker_info["company_name"],
                    "logo_url": ticker_info["logo_url"],
                    "_cache_key_placeholder": cache_key,
                }
            )

    if not symbols_to_fetch:
        return results  # All data was in cache

    # 2. Fetch data for symbols not found in cache using batching
    fetched_data_map = {}
    try:
        tickers_data = fetch_tickers_data_batched(symbols_to_fetch)
        if tickers_data:
            for symbol in symbols_to_fetch:
                ticker_obj = tickers_data.tickers.get(symbol)
                if ticker_obj:
                    try:
                        info = ticker_obj.info
                        # Fetch history for Open/Close - using period="1d" should be efficient enough for batch
                        history = ticker_obj.history(period="1d")
                        history_last_row_series = (
                            history.iloc[-1] if not history.empty else None
                        )

                        price = safe_get_info(info, "regularMarketPrice")
                        if price == "N/A" and history_last_row_series is not None:
                            price = safe_get_info(history_last_row_series, "Close")

                        open_price = (
                            safe_get_info(history_last_row_series, "Open")
                            if history_last_row_series is not None
                            else "N/A"
                        )
                        close_price = (
                            safe_get_info(history_last_row_series, "Close")
                            if history_last_row_series is not None
                            else "N/A"
                        )

                        fetched_data_map[symbol] = {
                            "price": price,
                            "open": open_price,
                            "close": close_price,
                            "change_percent": safe_get_info(
                                info, "regularMarketChangePercent"
                            ),
                            "market_cap": safe_get_info(info, "marketCap"),
                            "sector": safe_get_info(info, "sector"),
                        }
                    except Exception as e:
                        print(
                            f"Error processing fetched info/history for {symbol}: {e}",
                            flush=True,
                        )

    except Exception as e:
        print(
            f"Error during batch fetch for stock symbols with positions {symbols_to_fetch}: {e}",
            flush=True,
        )

    # 3. Update placeholders in results list and cache newly fetched data
    final_results = []
    for item in results:
        if "_cache_key_placeholder" in item:
            symbol = item["symbol"]
            original_info = next(
                info for info in tickers_info_list if info["symbol"] == symbol
            )  # Get original info

            fetched_item_data = fetched_data_map.get(symbol)

            if fetched_item_data:
                updated_item = {
                    "symbol": symbol,
                    "price": round(fetched_item_data["price"], 2)
                    if isinstance(fetched_item_data["price"], (int, float))
                    else "N/A",
                    "open": round(fetched_item_data["open"], 2)
                    if isinstance(fetched_item_data["open"], (int, float))
                    else "N/A",
                    "close": round(fetched_item_data["close"], 2)
                    if isinstance(fetched_item_data["close"], (int, float))
                    else "N/A",
                    "change_percent": round(
                        fetched_item_data["change_percent"] * 100, 2
                    )
                    if isinstance(fetched_item_data["change_percent"], (int, float))
                    else "N/A",
                    "market_cap": round(fetched_item_data["market_cap"])
                    if isinstance(fetched_item_data["market_cap"], (int, float))
                    else "N/A",
                    "sector": fetched_item_data["sector"],
                    "industry": original_info["company_name"],
                    "logo_url": original_info["logo_url"],
                }
                final_results.append(updated_item)
                await set_cached_data(
                    item["_cache_key_placeholder"],
                    updated_item,
                    CACHE_EXPIRY_SECONDS_SHORT,
                )
            else:
                final_results.append(
                    {
                        "symbol": symbol,
                        "price": "N/A",
                        "open": "N/A",
                        "close": "N/A",
                        "change_percent": "N/A",
                        "market_cap": "N/A",
                        "sector": "N/A",
                        "industry": original_info["company_name"],
                        "logo_url": original_info["logo_url"],
                    }
                )
        else:
            final_results.append(item)

    return final_results


# --- Helper to fetch exchange rate with retry and cache ---
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_exchange_rate_cached(
    from_currency: str, to_currency: str
) -> float | None:
    """Fetches exchange rate using yfinance with retries and caching."""
    cache_key = get_cache_key("exchange_rate", from_currency, to_currency)
    cached_rate = await get_cached_data(cache_key)

    if cached_rate is not None:
        print(
            f"Returning cached exchange rate for {from_currency} to {to_currency}: {cached_rate}",
            flush=True,
        )
        return cached_rate

    # Cache miss, fetch from yfinance
    yf_symbol = f"{from_currency.upper()}{to_currency.upper()}=X"
    print(f"Attempting to fetch exchange rate for {yf_symbol}...")
    try:
        ticker = yf.Ticker(yf_symbol)
        history = ticker.history(
            period="1d", interval="15m"
        )  # Use a recent interval for potentially more up-to-date rate
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
        )  # Cache rate for longer

        return rate

    except Exception as e:
        print(
            f"Failed to fetch exchange rate for {from_currency} to {to_currency} after retries: {e}",
            flush=True,
        )
        # This will be caught by the @retry, but if retries fail, the exception propagates
        # Let the calling function handle the None return or propagated exception
        return None


async def fetch_stock_data_crud_gbp(db: AsyncSession, tickers_info_list: List[Dict]):
    """
    Fetches current stock data and converts prices/market caps to GBP, using batching and caching.
    """
    if not tickers_info_list:
        return []

    # 1. Fetch USD to GBP conversion rate once with retries and cache
    usd_to_gbp_rate = await fetch_exchange_rate_cached("USD", "GBP")
    if usd_to_gbp_rate is None:
        print(
            "USD to GBP rate not available, cannot provide GBP converted data.",
            flush=True,
        )
        # Return list of N/A data if rate is unavailable
        return [
            {
                "symbol": item["symbol"],
                "price": "N/A",
                "change_percent": "N/A",
                "market_cap": "N/A",
                "sector": "N/A",
                "industry": item["company_name"],
                "logo_url": item["logo_url"],
            }
            for item in tickers_info_list
        ]

    results = []  # List to store final results (cached + fetched)
    symbols_to_fetch = []  # List of symbols not found in cache

    # 2. Check cache first for each symbol (GBP converted data)
    for ticker_info in tickers_info_list:
        symbol = ticker_info["symbol"]
        cache_key = get_cache_key("stock_current_gbp", symbol)
        cached_item = await get_cached_data(cache_key)

        if cached_item:
            results.append(cached_item)
        else:
            symbols_to_fetch.append(symbol)
            # Add a placeholder
            results.append(
                {
                    "symbol": symbol,
                    "price": "N/A",
                    "change_percent": "N/A",
                    "market_cap": "N/A",
                    "sector": "N/A",
                    "industry": ticker_info["company_name"],
                    "logo_url": ticker_info["logo_url"],
                    "_cache_key_placeholder": cache_key,
                }
            )

    if not symbols_to_fetch:
        return results  # All data was in cache

    # 3. Fetch USD data for symbols not found in cache using batching
    # We fetch USD data first, then convert to GBP
    fetched_usd_data_map = {}
    try:
        tickers_data = fetch_tickers_data_batched(symbols_to_fetch)
        if tickers_data:
            for symbol in symbols_to_fetch:
                ticker_obj = tickers_data.tickers.get(symbol)
                if ticker_obj:
                    try:
                        info = ticker_obj.info
                        price_usd = safe_get_info(info, "regularMarketPrice")
                        if price_usd == "N/A":
                            price_usd = safe_get_info(info, "previousClose")

                        fetched_usd_data_map[symbol] = {
                            "price_usd": price_usd,
                            "change_percent": safe_get_info(
                                info, "regularMarketChangePercent"
                            ),
                            "market_cap_usd": safe_get_info(info, "marketCap"),
                            "sector": safe_get_info(info, "sector"),
                        }
                    except Exception as e:
                        print(
                            f"Error processing fetched info for {symbol} (USD for GBP conv): {e}",
                            flush=True,
                        )

    except Exception as e:
        print(
            f"Error during batch fetch for stock symbols (USD for GBP conv) {symbols_to_fetch}: {e}",
            flush=True,
        )

    # 4. Convert fetched USD data to GBP, update placeholders, and cache
    final_results = []
    for item in results:
        if "_cache_key_placeholder" in item:
            symbol = item["symbol"]
            original_info = next(
                info for info in tickers_info_list if info["symbol"] == symbol
            )  # Get original info

            fetched_item_usd_data = fetched_usd_data_map.get(symbol)

            if fetched_item_usd_data:
                # Convert USD values to GBP if rate is available and USD data is valid
                price_gbp = "N/A"
                market_cap_gbp = "N/A"

                if (
                    usd_to_gbp_rate is not None
                ):  # Rate should be available at this point
                    price_usd = fetched_item_usd_data["price_usd"]
                    market_cap_usd = fetched_item_usd_data["market_cap_usd"]

                    if isinstance(price_usd, (int, float)):
                        price_gbp = round(price_usd * usd_to_gbp_rate, 2)
                    if isinstance(market_cap_usd, (int, float)):
                        market_cap_gbp = round(market_cap_usd * usd_to_gbp_rate)

                updated_item = {
                    "symbol": symbol,
                    "price": price_gbp,  # This is already GBP or N/A
                    "change_percent": round(
                        fetched_item_usd_data["change_percent"] * 100, 2
                    )
                    if isinstance(fetched_item_usd_data["change_percent"], (int, float))
                    else "N/A",
                    "market_cap": market_cap_gbp,  # This is already GBP or N/A
                    "sector": fetched_item_usd_data["sector"],
                    "industry": original_info["company_name"],
                    "logo_url": original_info["logo_url"],
                }
                final_results.append(updated_item)
                await set_cached_data(
                    item["_cache_key_placeholder"],
                    updated_item,
                    CACHE_EXPIRY_SECONDS_SHORT,
                )
            else:
                # Data not in cache and not successfully fetched (even in USD), keep placeholder
                final_results.append(
                    {
                        "symbol": symbol,
                        "price": "N/A",
                        "change_percent": "N/A",
                        "market_cap": "N/A",
                        "sector": "N/A",
                        "industry": original_info["company_name"],
                        "logo_url": original_info["logo_url"],
                    }
                )
        else:
            final_results.append(item)  # Item was from cache

    return final_results


async def fetch_stock_data_crud_gbp_with_positions(
    db: AsyncSession,
    tickers_info_list: List[
        Dict
    ],  # currency parameter seems unused based on original logic
):
    """
    Fetches stock data including open/close prices and converts to GBP, using batching and caching.
    """
    if not tickers_info_list:
        return []

    # 1. Fetch USD to GBP conversion rate once with retries and cache
    usd_to_gbp_rate = await fetch_exchange_rate_cached("USD", "GBP")
    if usd_to_gbp_rate is None:
        print(
            "USD to GBP rate not available, cannot provide GBP converted data with positions.",
            flush=True,
        )
        # Return list of N/A data if rate is unavailable
        return [
            {
                "symbol": item["symbol"],
                "price": "N/A",
                "open": "N/A",
                "close": "N/A",
                "change_percent": "N/A",
                "market_cap": "N/A",
                "sector": "N/A",
                "industry": item["company_name"],
                "logo_url": item["logo_url"],
            }
            for item in tickers_info_list
        ]

    results = []  # List to store final results (cached + fetched)
    symbols_to_fetch = []  # List of symbols not found in cache

    # 2. Check cache first for each symbol (GBP converted data with positions)
    for ticker_info in tickers_info_list:
        symbol = ticker_info["symbol"]
        cache_key = get_cache_key("stock_current_pos_gbp", symbol)
        cached_item = await get_cached_data(cache_key)

        if cached_item:
            results.append(cached_item)
        else:
            symbols_to_fetch.append(symbol)
            # Add a placeholder
            results.append(
                {
                    "symbol": symbol,
                    "price": "N/A",
                    "open": "N/A",
                    "close": "N/A",
                    "change_percent": "N/A",
                    "market_cap": "N/A",
                    "sector": "N/A",
                    "industry": ticker_info["company_name"],
                    "logo_url": ticker_info["logo_url"],
                    "_cache_key_placeholder": cache_key,
                }
            )

    if not symbols_to_fetch:
        return results  # All data was in cache

    # 3. Fetch USD data for symbols not found in cache using batching (including history for positions)
    fetched_usd_data_map = {}
    try:
        tickers_data = fetch_tickers_data_batched(symbols_to_fetch)
        if tickers_data:
            for symbol in symbols_to_fetch:
                ticker_obj = tickers_data.tickers.get(symbol)
                if ticker_obj:
                    try:
                        info = ticker_obj.info
                        # Fetch history for Open/Close
                        history = ticker_obj.history(period="1d")
                        history_last_row_series = (
                            history.iloc[-1] if not history.empty else None
                        )

                        price_usd = safe_get_info(info, "regularMarketPrice")
                        if price_usd == "N/A" and history_last_row_series is not None:
                            price_usd = safe_get_info(history_last_row_series, "Close")

                        open_usd = (
                            safe_get_info(history_last_row_series, "Open")
                            if history_last_row_series is not None
                            else "N/A"
                        )
                        close_usd = (
                            safe_get_info(history_last_row_series, "Close")
                            if history_last_row_series is not None
                            else "N/A"
                        )

                        fetched_usd_data_map[symbol] = {
                            "price_usd": price_usd,
                            "open_usd": open_usd,
                            "close_usd": close_usd,
                            "change_percent": safe_get_info(
                                info, "regularMarketChangePercent"
                            ),
                            "market_cap_usd": safe_get_info(info, "marketCap"),
                            "sector": safe_get_info(info, "sector"),
                        }
                    except Exception as e:
                        print(
                            f"Error processing fetched info/history for {symbol} (USD for GBP pos conv): {e}",
                            flush=True,
                        )

    except Exception as e:
        print(
            f"Error during batch fetch for stock symbols with positions (USD for GBP pos conv) {symbols_to_fetch}: {e}",
            flush=True,
        )

    # 4. Convert fetched USD data to GBP, update placeholders, and cache
    final_results = []
    for item in results:
        if "_cache_key_placeholder" in item:
            symbol = item["symbol"]
            original_info = next(
                info for info in tickers_info_list if info["symbol"] == symbol
            )  # Get original info

            fetched_item_usd_data = fetched_usd_data_map.get(symbol)

            if fetched_item_usd_data:
                # Convert USD values to GBP if rate is available and USD data is valid
                price_gbp = "N/A"
                open_gbp = "N/A"
                close_gbp = "N/A"
                market_cap_gbp = "N/A"

                if usd_to_gbp_rate is not None:  # Rate should be available
                    price_usd = fetched_item_usd_data["price_usd"]
                    open_usd = fetched_item_usd_data["open_usd"]
                    close_usd = fetched_item_usd_data["close_usd"]
                    market_cap_usd = fetched_item_usd_data["market_cap_usd"]

                    if isinstance(price_usd, (int, float)):
                        price_gbp = round(price_usd * usd_to_gbp_rate, 2)
                    if isinstance(open_usd, (int, float)):
                        open_gbp = round(open_usd * usd_to_gbp_rate, 2)
                    if isinstance(close_usd, (int, float)):
                        close_gbp = round(close_usd * usd_to_gbp_rate, 2)
                    if isinstance(market_cap_usd, (int, float)):
                        market_cap_gbp = round(market_cap_usd * usd_to_gbp_rate)

                updated_item = {
                    "symbol": symbol,
                    "price": price_gbp,
                    "open": open_gbp,
                    "close": close_gbp,
                    "change_percent": round(
                        fetched_item_usd_data["change_percent"] * 100, 2
                    )
                    if isinstance(fetched_item_usd_data["change_percent"], (int, float))
                    else "N/A",
                    "market_cap": market_cap_gbp,
                    "sector": fetched_item_usd_data["sector"],
                    "industry": original_info["company_name"],
                    "logo_url": original_info["logo_url"],
                }
                final_results.append(updated_item)
                await set_cached_data(
                    item["_cache_key_placeholder"],
                    updated_item,
                    CACHE_EXPIRY_SECONDS_SHORT,
                )
            else:
                final_results.append(
                    {
                        "symbol": symbol,
                        "price": "N/A",
                        "open": "N/A",
                        "close": "N/A",
                        "change_percent": "N/A",
                        "market_cap": "N/A",
                        "sector": "N/A",
                        "industry": original_info["company_name"],
                        "logo_url": original_info["logo_url"],
                    }
                )
        else:
            final_results.append(item)  # Item was from cache

    return final_results


# --- Historical Data Functions (now with caching) ---

# Note: These functions are still synchronous (no `async` keyword) but use
# blocking libraries. If called from an `async def` endpoint, they should
# be run in a thread pool executor using `asyncio.to_thread`.
# The cache functions they call (`get_cached_data`, `set_cached_data`)
# are asynchronous, so these historical data functions would need to be async too
# to `await` them. Let's convert them to async to properly use async cache.


async def fetch_historical_data(symbol: str, currency: str):
    """
    Fetches historical data for a crypto symbol using yfinance and caching.
    """
    yf_symbol = f"{symbol}-{currency.upper()}"
    timeframes = {
        "1 Day": ("1d", "15m"),
        "1 Week": ("7d", "1h"),
        "1 Month": ("1mo", "1d"),
        "3 Months": ("3mo", "1d"),
        "1 Year": ("1y", "1wk"),
        "5 Years": ("5y", "1mo"),
    }
    data = {}  # Result dictionary

    for label, (period, interval) in timeframes.items():
        # 1. Check cache for this specific timeframe
        cache_key = get_cache_key("crypto_hist", symbol, currency, period, interval)
        cached_hist = await get_cached_data(cache_key)

        if cached_hist:
            data[label] = cached_hist
            print(
                f"Returning cached historical data for {yf_symbol} ({label})",
                flush=True,
            )
            continue  # Move to next timeframe

        # 2. Cache miss, fetch from yfinance with retries
        try:
            history = fetch_historical_data_single_ticker(yf_symbol, period, interval)

            if history.empty:
                print(f"Historical data empty for {yf_symbol} ({label})", flush=True)
                data[label] = {"error": f"Data empty for {label}"}
                # Optionally cache empty/error state for a short period
                # await set_cached_data(cache_key, data[label], CACHE_EXPIRY_SECONDS_SHORT)
                continue

            entries = []
            # Adjust step based on history length to avoid huge payloads
            step = max(len(history) // 70, 1) if len(history) > 70 else 1
            indices_to_include = list(range(0, len(history), step))
            if (len(history) > 0) and ((len(history) - 1) not in indices_to_include):
                indices_to_include.append(len(history) - 1)
            indices_to_include.sort()

            for i in indices_to_include:
                if i < 0 or i >= len(history):
                    continue

                current_price = history.iloc[i]["Close"]
                # Determine the previous point for change calculation
                prev_idx = max(
                    0, i - step
                )  # Go back 'step' intervals, but not before start
                prev_price = (
                    history.iloc[prev_idx]["Close"]
                    if len(history) > prev_idx
                    else current_price
                )  # Fallback if prev_idx is out of bounds or 0

                change = (
                    round(current_price - prev_price, 2)
                    if isinstance(current_price, (int, float))
                    and isinstance(prev_price, (int, float))
                    else "N/A"
                )
                percent_change = (
                    round((change / prev_price) * 100, 2)
                    if isinstance(change, (int, float))
                    and isinstance(prev_price, (int, float))
                    and prev_price != 0
                    else 0
                )

                # Ensure values are numbers or "N/A"
                if (
                    isinstance(current_price, (int, float))
                    and current_price == current_price
                ):
                    current_price_formatted = round(current_price, 2)
                else:
                    current_price_formatted = "N/A"

                entries.append(
                    {
                        "Time": history.index[
                            i
                        ].isoformat(),  # Use ISO format for datetime
                        "Price": current_price_formatted,
                        "Change": change
                        if isinstance(change, (int, float)) and change == change
                        else "N/A",
                        "% Change": percent_change
                        if isinstance(percent_change, (int, float))
                        and percent_change == percent_change
                        else "N/A",
                    }
                )
            data[label] = entries
            # 3. Cache the fetched data for this timeframe
            await set_cached_data(cache_key, entries, CACHE_EXPIRY_SECONDS_LONG)

        except Exception as e:
            print(
                f"Data fetch failed for {yf_symbol} ({label}) after retries: {e}",
                flush=True,
            )
            data[label] = {"error": f"Data fetch failed for {label}: {e}"}

    return data


async def fetch_historical_data_stock(symbol: str, currency: str):
    """
    Fetches historical data for a stock symbol using yfinance and caching.
    Currency parameter is unused in original logic, keeping it for signature compatibility.
    """
    yf_symbol = symbol
    timeframes = {
        "1 Day": ("1d", "15m"),
        "1 Week": ("7d", "1h"),
        "1 Month": ("1mo", "1d"),
        "3 Months": ("3mo", "1d"),
        "1 Year": ("1y", "1wk"),
        "5 Years": ("5y", "1mo"),
    }
    data = {}

    for label, (period, interval) in timeframes.items():
        # 1. Check cache
        cache_key = get_cache_key(
            "stock_hist", symbol, period=period, interval=interval
        )
        cached_hist = await get_cached_data(cache_key)

        if cached_hist:
            data[label] = cached_hist
            print(
                f"Returning cached historical data for {yf_symbol} ({label})",
                flush=True,
            )
            continue  # Move to next timeframe

        # 2. Cache miss, fetch from yfinance with retries
        try:
            history = fetch_historical_data_single_ticker(yf_symbol, period, interval)

            if history.empty:
                print(f"Historical data empty for {yf_symbol} ({label})", flush=True)
                data[label] = {"error": f"Data empty for {label}"}
                # Optionally cache empty/error state
                # await set_cached_data(cache_key, data[label], CACHE_EXPIRY_SECONDS_SHORT)
                continue

            entries = []
            step = max(len(history) // 70, 1) if len(history) > 70 else 1
            indices_to_include = list(range(0, len(history), step))
            if (len(history) > 0) and ((len(history) - 1) not in indices_to_include):
                indices_to_include.append(len(history) - 1)
            indices_to_include.sort()

            for i in indices_to_include:
                if i < 0 or i >= len(history):
                    continue

                current_price = history.iloc[i]["Close"]
                prev_idx = max(0, i - step)
                prev_price = (
                    history.iloc[prev_idx]["Close"]
                    if len(history) > prev_idx
                    else current_price
                )

                change = (
                    round(current_price - prev_price, 2)
                    if isinstance(current_price, (int, float))
                    and isinstance(prev_price, (int, float))
                    else "N/A"
                )
                percent_change = (
                    round((change / prev_price) * 100, 2)
                    if isinstance(change, (int, float))
                    and isinstance(prev_price, (int, float))
                    and prev_price != 0
                    else 0
                )

                if (
                    isinstance(current_price, (int, float))
                    and current_price == current_price
                ):
                    current_price_formatted = round(current_price, 2)
                else:
                    current_price_formatted = "N/A"

                entries.append(
                    {
                        "Time": history.index[i].isoformat(),  # Use ISO format
                        "Price": current_price_formatted,
                        "Change": change
                        if isinstance(change, (int, float)) and change == change
                        else "N/A",
                        "% Change": percent_change
                        if isinstance(percent_change, (int, float))
                        and percent_change == percent_change
                        else "N/A",
                    }
                )
            data[label] = entries
            # 3. Cache the fetched data
            await set_cached_data(cache_key, entries, CACHE_EXPIRY_SECONDS_LONG)

        except Exception as e:
            print(
                f"Data fetch failed for {yf_symbol} ({label}) after retries: {e}",
                flush=True,
            )
            data[label] = {"error": f"Data fetch failed for {label}: {e}"}

    return data


async def fetch_historical_data_stock_gbp(symbol: str):
    """
    Fetches historical data for a stock symbol, converts prices to GBP, using yfinance and caching.
    """
    yf_symbol = symbol
    timeframes = {
        "1 Day": ("1d", "15m"),
        "1 Week": ("7d", "1h"),
        "1 Month": ("1mo", "1d"),
        "3 Months": ("3mo", "1d"),
        "1 Year": ("1y", "1wk"),
        "5 Years": ("5y", "1mo"),
    }
    data = {}

    # 1. Fetch USD to GBP conversion rate once with retries and cache
    usd_to_gbp_rate = await fetch_exchange_rate_cached("USD", "GBP")
    if usd_to_gbp_rate is None:
        print(
            "USD to GBP rate not available, cannot provide GBP historical data.",
            flush=True,
        )
        # If rate is unavailable, return errors for all timeframes
        for label in timeframes:
            data[label] = {"error": "Exchange rate unavailable"}
        return data

    for label, (period, interval) in timeframes.items():
        # 2. Check cache for this specific timeframe (GBP converted)
        cache_key = get_cache_key(
            "stock_hist_gbp", symbol, period=period, interval=interval
        )
        cached_hist = await get_cached_data(cache_key)

        if cached_hist:
            data[label] = cached_hist
            print(
                f"Returning cached historical data for {yf_symbol} ({label}, GBP)",
                flush=True,
            )
            continue  # Move to next timeframe

        # 3. Cache miss, fetch USD data from yfinance with retries
        try:
            history_usd = fetch_historical_data_single_ticker(
                yf_symbol, period, interval
            )

            if history_usd.empty:
                print(
                    f"Historical data empty for {yf_symbol} ({label}, USD for GBP conv)",
                    flush=True,
                )
                data[label] = {"error": f"Data empty for {label}"}
                # Optionally cache empty/error state
                # await set_cached_data(cache_key, data[label], CACHE_EXPIRY_SECONDS_SHORT)
                continue

            entries_gbp = []
            step = max(len(history_usd) // 70, 1) if len(history_usd) > 70 else 1
            indices_to_include = list(range(0, len(history_usd), step))
            if (len(history_usd) > 0) and (
                (len(history_usd) - 1) not in indices_to_include
            ):
                indices_to_include.append(len(history_usd) - 1)
            indices_to_include.sort()

            for i in indices_to_include:
                if i < 0 or i >= len(history_usd):
                    continue

                current_price_usd = history_usd.iloc[i]["Close"]
                prev_idx = max(0, i - step)
                prev_price_usd = (
                    history_usd.iloc[prev_idx]["Close"]
                    if len(history_usd) > prev_idx
                    else current_price_usd
                )

                # Convert USD Price & Calculate Change in GBP
                current_price_gbp = "N/A"
                change_gbp = "N/A"
                percent_change_gbp = "N/A"

                if (
                    isinstance(current_price_usd, (int, float))
                    and current_price_usd == current_price_usd
                ):
                    current_price_gbp = round(current_price_usd * usd_to_gbp_rate, 2)

                    if (
                        isinstance(prev_price_usd, (int, float))
                        and prev_price_usd == prev_price_usd
                        and prev_price_usd != 0
                    ):
                        prev_price_gbp = round(prev_price_usd * usd_to_gbp_rate, 2)
                        change_gbp = round(current_price_gbp - prev_price_gbp, 2)
                        # Calculate percent change based on GBP prices
                        percent_change_gbp = round(
                            (change_gbp / prev_price_gbp) * 100, 2
                        )
                    else:
                        change_gbp = 0.0
                        percent_change_gbp = 0.0

                entries_gbp.append(
                    {
                        "Time": history_usd.index[i].isoformat(),  # Use ISO format
                        "Price": current_price_gbp,
                        "Change": change_gbp,
                        " % Change": percent_change_gbp,  # Keep the original key name
                    }
                )

            data[label] = entries_gbp
            # 4. Cache the fetched and converted GBP data
            await set_cached_data(cache_key, entries_gbp, CACHE_EXPIRY_SECONDS_LONG)

        except Exception as e:
            print(
                f"Data fetch or conversion failed for {yf_symbol} ({label}, GBP conversion) after retries: {e}",
                flush=True,
            )
            data[label] = {"error": f"Data fetch/conversion failed for {label}: {e}"}

    return data


# import requests
# from sqlalchemy.ext.asyncio import AsyncSession
# from typing import List
# import yfinance as yf
# from forex_python.converter import CurrencyRates


# async def fetch_crypto_data_crud(db: AsyncSession, symbols: List[str], currency: str):
#     data = []
    
    
#     for symbol in symbols:
#         image = symbol["image"]
#         symbol = symbol["symbol"]

#         try:
#             crypto = yf.Ticker(f"{symbol}-{currency}")
#             history = crypto.history(period="1d", interval="1h").iloc[-1]
#             info = crypto.info

#             data.append(
#                 {
#                     "symbol": symbol,
#                     "price": round(history["Close"], 2),
#                     "market_cap": round(info.get("marketCap", "N/A")),
#                     "change_percent": round(
#                         info.get("regularMarketChangePercent", 0), 2
#                     ),
#                     "logo_url": image
#                 }
#             )
#         except Exception:
#             data.append(
#                 {
#                     "symbol": symbol,
#                     "price": "N/A",
#                     "market_cap": "N/A",
#                     "change_percent": "N/A",
#                     "logo_url": "N/A",  # Default in case of failure
#                 }
#             )

#     return data


# async def fetch_stock_data_crud(db: AsyncSession, tickers: List[str]):
#     data = []
    
#     for ticker_info in tickers:
#         image = ticker_info["logo_url"]
#         ticker = ticker_info["symbol"]
#         company_name = ticker_info["company_name"]
        
#         try:
#             stock = yf.Ticker(ticker)
#             history = stock.history(period="1d").iloc[-1]
#             info = stock.info
            
#             # Only the specified fields
#             data.append({
#                 "symbol": ticker,
#                 "price": round(history["Close"], 2),
#                 "change_percent": round(info.get("regularMarketChangePercent", 0) * 100, 2),
#                 "market_cap": round(info.get("marketCap", 0)),
#                 "sector": info.get("sector", "N/A"),
#                 "industry": company_name,
#                 "logo_url": image
#             })
#         except Exception as e:
#             data.append({
#                 "symbol": ticker,
#                 "price": "N/A",
#                 "change_percent": "N/A",
#                 "market_cap": "N/A",
#                 "sector": "N/A",
#                 "industry": "N/A",
#                 "logo_url": "N/A"
#             })
            
#     return data


# async def fetch_stock_data_crud_with_positions(db: AsyncSession, tickers: List[str]):
#     data = []

#     for ticker_info in tickers:
#         image = ticker_info["logo_url"]
#         ticker = ticker_info["symbol"]
#         company_name = ticker_info["company_name"]

#         try:
#             stock = yf.Ticker(ticker)
#             history = stock.history(period="1d").iloc[-1]
#             info = stock.info

#             # Including open and close prices
#             data.append(
#                 {
#                     "symbol": ticker,
#                     "price": round(history["Close"], 2),
#                     "open": round(history["Open"], 2),
#                     "close": round(history["Close"], 2),
#                     "change_percent": round(
#                         info.get("regularMarketChangePercent", 0) * 100, 2
#                     ),
#                     "market_cap": round(info.get("marketCap", 0)),
#                     "sector": info.get("sector", "N/A"),
#                     "industry": company_name,
#                     "logo_url": image,
#                 }
#             )
#         except Exception as e:
#             data.append(
#                 {
#                     "symbol": ticker,
#                     "price": "N/A",
#                     "open": "N/A",
#                     "close": "N/A",
#                     "change_percent": "N/A",
#                     "market_cap": "N/A",
#                     "sector": "N/A",
#                     "industry": "N/A",
#                     "logo_url": "N/A",
#                 }
#             )

#     return data


# async def fetch_stock_data_crud_gbp(db: AsyncSession, tickers: List[str], currency="USD"):
#     data = []

#     # Fetch USD to GBP conversion using yfinance
#     usd_to_gbp_rate = 1 / yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1]

#     # usd_to_gbp_rate = (
#     #     yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1]
#     #     if currency == "GBP"
#     #     else 1.0
#     # )

#     for ticker_info in tickers:
#         image = ticker_info["logo_url"]
#         ticker = ticker_info["symbol"]
#         company_name = ticker_info["company_name"]

#         try:
#             stock = yf.Ticker(ticker)
#             history = stock.history(period="1d").iloc[-1]
#             info = stock.info

#             price = round(history["Close"] * usd_to_gbp_rate, 2)

#             data.append(
#                 {
#                     "symbol": ticker,
#                     "price": price,
#                     "change_percent": round(
#                         info.get("regularMarketChangePercent", 0) * 100, 2
#                     ),
#                     "market_cap": round(info.get("marketCap", 0) * usd_to_gbp_rate),
#                     "sector": info.get("sector", "N/A"),
#                     "industry": company_name,
#                     "logo_url": image,
#                 }
#             )
#         except Exception as e:
#             data.append(
#                 {
#                     "symbol": ticker,
#                     "price": "N/A",
#                     "change_percent": "N/A",
#                     "market_cap": "N/A",
#                     "sector": "N/A",
#                     "industry": "N/A",
#                     "logo_url": "N/A",
#                 }
#             )

#     return data

# async def fetch_stock_data_crud_gbp_with_positions(
#     db: AsyncSession, tickers: List[str], currency="USD"
# ):
#     data = []

#     # Fetch USD to GBP conversion using yfinance
#     usd_to_gbp_rate = 1 / yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1]

#     for ticker_info in tickers:
#         image = ticker_info["logo_url"]
#         ticker = ticker_info["symbol"]
#         company_name = ticker_info["company_name"]

#         try:
#             stock = yf.Ticker(ticker)
#             history = stock.history(period="1d").iloc[-1]
#             info = stock.info

#             price = round(history["Close"] * usd_to_gbp_rate, 2)

#             data.append(
#                 {
#                     "symbol": ticker,
#                     "price": price,
#                     "open": round(history["Open"] * usd_to_gbp_rate, 2),
#                     "close": round(history["Close"] * usd_to_gbp_rate, 2),
#                     "change_percent": round(
#                         info.get("regularMarketChangePercent", 0) * 100, 2
#                     ),
#                     "market_cap": round(info.get("marketCap", 0) * usd_to_gbp_rate),
#                     "sector": info.get("sector", "N/A"),
#                     "industry": company_name,
#                     "logo_url": image,
#                 }
#             )
#         except Exception as e:
#             data.append(
#                 {
#                     "symbol": ticker,
#                     "price": "N/A",
#                     "open": "N/A",
#                     "close": "N/A",
#                     "change_percent": "N/A",
#                     "market_cap": "N/A",
#                     "sector": "N/A",
#                     "industry": "N/A",
#                     "logo_url": "N/A",
#                 }
#             )

#     return data


# def fetch_historical_data(symbol, currency):
#     # symbol = symbol["symbol"]
#     try:
#         crypto = yf.Ticker(f"{symbol}-{currency}")
#         timeframes = {
#             "1 Day": ("1d", "15m"),
#             "1 Week": ("7d", "1h"),
#             "1 Month": ("1mo", "1d"),
#             "3 Months": ("3mo", "1d"),
#             "1 Year": ("1y", "1wk"),
#             "5 Years": ("5y", "1mo"),
#         }
#         data = {}
#         for label, (period, interval) in timeframes.items():
#             history = crypto.history(period=period, interval=interval)
#             entries = []
#             step = max(len(history) // 70, 1)
#             for i in range(0, len(history), step):
#                 current_price = history.iloc[i]["Close"]
#                 prev_price = history.iloc[i - 1]["Close"] if i > 0 else current_price
#                 change = round(current_price - prev_price, 2)
#                 percent_change = (
#                     round((change / prev_price) * 100, 2) if prev_price != 0 else 0
#                 )
#                 entries.append(
#                     {
#                         "Time": history.index[i],
#                         "Price": round(current_price, 2),
#                         "Change": change,
#                         "% Change": percent_change,
#                     }
#                 )
#             data[label] = entries
#         return data
#     except Exception:
#         return {"error": "Data fetch failed"}
    

# def fetch_historical_data_stock(symbol, currency):
#     # symbol = symbol["symbol"]
#     try:
#         crypto = yf.Ticker(f"{symbol}")
#         timeframes = {
#             "1 Day": ("1d", "15m"),
#             "1 Week": ("7d", "1h"),
#             "1 Month": ("1mo", "1d"),
#             "3 Months": ("3mo", "1d"),
#             "1 Year": ("1y", "1wk"),
#             "5 Years": ("5y", "1mo"),
#         }
#         data = {}
#         for label, (period, interval) in timeframes.items():
#             history = crypto.history(period=period, interval=interval)
#             entries = []
#             step = max(len(history) // 70, 1)
#             for i in range(0, len(history), step):
#                 current_price = history.iloc[i]["Close"]
#                 prev_price = history.iloc[i - 1]["Close"] if i > 0 else current_price
#                 change = round(current_price - prev_price, 2)
#                 percent_change = (
#                     round((change / prev_price) * 100, 2) if prev_price != 0 else 0
#                 )
#                 entries.append(
#                     {
#                         "Time": history.index[i],
#                         "Price": round(current_price, 2),
#                         "Change": change,
#                         "% Change": percent_change,
#                     }
#                 )
#             data[label] = entries
#         return data
#     except Exception:
#         return {"error": "Data fetch failed"}
    
# def fetch_historical_data_stock_gbp(symbol):
#     try:
#         crypto = yf.Ticker(symbol)
#         usd_to_gbp_rate = (
#             1 / yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1]
#         )

#         timeframes = {
#             "1 Day": ("1d", "15m"),
#             "1 Week": ("7d", "1h"),
#             "1 Month": ("1mo", "1d"),
#             "3 Months": ("3mo", "1d"),
#             "1 Year": ("1y", "1wk"),
#             "5 Years": ("5y", "1mo"),
#         }

#         data = {}
#         for label, (period, interval) in timeframes.items():
#             history = crypto.history(period=period, interval=interval)
#             entries = []

#             step = max(len(history) // 70, 1)
#             for i in range(0, len(history), step):
#                 current_price_usd = history.iloc[i]["Close"]
#                 prev_price_usd = (
#                     history.iloc[i - 1]["Close"] if i > 0 else current_price_usd
#                 )

#                 # GBP Price & Change Calculation
#                 current_price_gbp = round(current_price_usd * usd_to_gbp_rate, 2)
#                 prev_price_gbp = round(prev_price_usd * usd_to_gbp_rate, 2)

#                 change_gbp = round(current_price_gbp - prev_price_gbp, 2)
#                 percent_change_gbp = (
#                     round((change_gbp / prev_price_gbp) * 100, 2)
#                     if prev_price_gbp != 0
#                     else 0
#                 )

#                 entries.append(
#                     {
#                         "Time": history.index[i],
#                         "Price": current_price_gbp,
#                         "Change": change_gbp,
#                         "% Change": percent_change_gbp,
#                     }
#                 )

#             data[label] = entries
#         return data

#     except Exception as e:
#         return {"error": f"Data fetch failed: {str(e)}"}