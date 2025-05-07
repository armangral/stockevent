import asyncio
import json  # Might be needed for cache interactions if not fully handled by cache module
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession  # Needed for create_user_alert
from sqlalchemy import select
from sqlalchemy.orm import Session  # Import sync Session type hint
from celery_config import celery

from app.core.db import (
    SessionLocal,
    SyncSessionLocal,
)  # Use SyncSessionLocal for sync Celery task
from app.models.user_alert import UserAlert
from app.schemas.user_alert import UserAlertCreate
from app.utils import send_email_alert  # This is an async function
import yfinance as yf

# Import retry decorators and caching functions
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.cache import (
    get_cached_data,  # Note: need a sync version or run async one in executor for sync context
    set_cached_data,  # Note: need a sync version or run async one in executor for sync context
    get_cache_key,
    CACHE_EXPIRY_SECONDS_SHORT,
    # CACHE_EXPIRY_SECONDS_MEDIUM, # Not strictly needed here
)


# --- Helper to run async code from sync ---
# Your existing asyncio.run() is fine for this simple case within a Celery task.
# If you needed to run multiple async calls concurrently within the task,
# you might set up an event loop once and run multiple coroutines.
def run_async_in_sync(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# --- Retry Decorator for yfinance calls in sync context ---
# Adjust stop and wait parameters based on observed rate limit behavior
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=30))
def fetch_tickers_info_batched_sync(yf_symbols: list[str]) -> dict[str, dict]:
    """
    Fetch info for multiple tickers using yf.Tickers with retries (synchronous context).
    Returns a dictionary mapping yf_symbol -> info dictionary.
    """
    if not yf_symbols:
        print("Called fetch_tickers_info_batched_sync with empty symbol list.")
        return {}
    print(
        f"Attempting batched info fetch for {len(yf_symbols)} symbols in sync task..."
    )
    try:
        # Using yf.Tickers is the recommended way for multiple symbols
        tickers_data = yf.Tickers(yf_symbols)
        # Accessing the .tickers attribute itself triggers fetching info for all
        # in the batch according to yfinance documentation.
        # We can return the info dicts directly.
        return {
            sym: ticker_data.info for sym, ticker_data in tickers_data.tickers.items()
        }
    except Exception as e:
        print(f"Error during batched info fetch for {yf_symbols}: {e}", flush=True)
        raise  # Re-raise to trigger retry


# --- Helper to safely get data from info dict (can reuse from crypto.py if in shared util) ---
def safe_get_info(info: dict, key: str, default: any = "N/A"):
    """Safely get a value from the ticker info dictionary."""
    if not isinstance(info, dict):
        return default
    value = info.get(key, default)
    if value is None or (
        isinstance(value, float) and value != value
    ):  # Check for NaN using value != value
        return default
    return value


# --- Create Alert (remains async as it's used in FastAPI endpoint) ---
async def create_user_alert(
    db: AsyncSession, alert_data: UserAlertCreate, email: EmailStr
):
    existing_alert = await db.execute(
        select(UserAlert).where(
            UserAlert.email.ilike(email),  # Case-insensitive email check
            UserAlert.symbol.ilike(alert_data.symbol),  # Case-insensitive symbol check
            UserAlert.target_price == alert_data.target_price,
            UserAlert.is_active
            == True,  # Consider if you allow setting alert for inactive duplicates
        )
    )
    if existing_alert.scalar_one_or_none():  # Use scalar_one_or_none
        raise HTTPException(
            status_code=400,
            detail=f"Alert for {alert_data.symbol} at {alert_data.target_price} already exists",
        )

    alert = UserAlert(
        email=email,
        symbol=alert_data.symbol.upper(),  # Store symbol consistently uppercase
        target_price=alert_data.target_price,
        is_active=True,  # Ensure new alerts are active by default
    )
    db.add(alert)
    await db.commit()  # Commit changes if this function is standalone
    await db.refresh(alert)
    return alert


# --- Celery Task (Synchronous) ---


@celery.task
def run_price_check():
    """
    Celery task to check prices for active alerts using batched yfinance calls and caching.
    """
    print("Starting celery alerts check...", flush=True)

    # Need to use a sync session within the sync Celery task
    with SyncSessionLocal() as db:
        # 1. Fetch all active alerts
        alerts: list[UserAlert] = (
            db.execute(select(UserAlert).where(UserAlert.is_active == True))
            .scalars()
            .all()
        )

        if not alerts:
            print("No active alerts to check.", flush=True)
            return

        print(f"Found {len(alerts)} active alerts.", flush=True)

        # 2. Collect unique symbols from active alerts
        # yfinance symbols might need '-USD' for crypto
        unique_yf_symbols = set()
        alert_symbol_map: dict[
            str, list[UserAlert]
        ] = {}  # Map yf_symbol to list of alerts for it

        for alert in alerts:
            # Determine the yfinance symbol format
            # Assuming all symbols in alerts are stocks or crypto that work with '-USD' suffix
            # You might need a way to differentiate stocks vs crypto based on user input or another field
            # For now, assuming crypto needs -USD, stocks don't. This is a simplification.
            # A more robust solution might store type ('stock'/'crypto') in the alert model.
            # Based on the `type` column added in migration 645703b15baa, you should use that!
            # Let's modify the UserAlert model to have a 'type' column.
            # ASSUMPTION: UserAlert model now has a 'type' column ('stocks' or 'crypto')

            # === IF UserAlert has a 'type' column ===
            # if alert.type.lower() == 'crypto':
            #     yf_symbol = f"{alert.symbol.upper()}-USD" # Assuming crypto alerts are USD based
            # else: # stocks
            #     yf_symbol = alert.symbol.upper()
            # =========================================

            # === Fallback if UserAlert does NOT have a 'type' column ===
            # You would need a way to know if it's crypto or stock.
            # Maybe check if the symbol is in your crypto_symbols list? Less robust.
            # Let's assume for simplicity that symbols ending in -USD are crypto, otherwise stocks.
            # This is NOT ideal. You should add a 'type' column to UserAlert.
            yf_symbol = alert.symbol.upper()
            # A common pattern is to add -USD for crypto unless it's a foreign stock
            # For robustness, let's assume symbols starting with 'BTC', 'ETH', etc. are crypto needing -USD
            # This is still heuristic. The 'type' column is strongly recommended.
            crypto_prefixes = [
                "BTC",
                "ETH",
                "BNB",
                "SOL",
                "XRP",
                "ADA",
                "AVAX",
                "DOGE",
                "DOT",
                "MATIC",
            ]  # Add more
            is_potential_crypto = any(
                yf_symbol.startswith(prefix) for prefix in crypto_prefixes
            )

            # This is still a guess. A 'type' column is best.
            # If you don't have a type, yfinance is less reliable for auto-detecting.
            # Let's try fetching both versions and see which one works? No, that's too many calls.
            # Let's stick to the heuristic for now, but note it's a weakness.
            if is_potential_crypto:
                yf_symbol_formatted = (
                    f"{yf_symbol}-USD"  # Hardcoded USD for crypto alerts
                )
            else:
                yf_symbol_formatted = yf_symbol  # Assume stocks are standard symbols

            unique_yf_symbols.add(yf_symbol_formatted)

            if yf_symbol_formatted not in alert_symbol_map:
                alert_symbol_map[yf_symbol_formatted] = []
            alert_symbol_map[yf_symbol_formatted].append(alert)
            # =========================================

        yf_symbols_list = list(unique_yf_symbols)
        print(f"Unique yfinance symbols to check: {yf_symbols_list}", flush=True)

        # 3. Fetch current prices for all unique symbols in a batch with retries
        # Need a synchronous way to get/set cache data within this sync task
        # If app.core.cache uses async redis client, you can't await here directly.
        # You need a sync wrapper or run async cache calls in an executor.
        # For simplicity, let's assume cache functions are blocking or use a blocking client here, or
        # we run the async cache calls within `run_async_in_sync` when fetching/setting prices.
        # Running fetch_tickers_info_batched_sync is blocking anyway, so let's make cache sync for this task.
        # ALTERNATIVE: Create separate sync cache functions in app.core.cache.py
        # Let's use run_async_in_sync to call the async cache functions for simplicity for now.

        symbol_prices: dict[str, float] = {}  # Map original symbol to fetched price

        # Collect symbols for which we need to fetch from yfinance
        symbols_to_fetch_yf = []
        for yf_symbol in yf_symbols_list:
            # Check cache for the price of this specific yf_symbol
            # Using a cache key prefix specific to the alerts task
            cache_key = get_cache_key("alert_price", yf_symbol)
            # Run async get_cached_data in sync context
            cached_price = run_async_in_sync(get_cached_data(cache_key))

            if cached_price is not None and isinstance(cached_price, (int, float)):
                # Cache stores the price, add to our map
                # Need to map back to the original alert symbol (without -USD)
                original_symbol = yf_symbol.replace(
                    "-USD", ""
                )  # Simple reverse mapping
                symbol_prices[original_symbol] = cached_price
            else:
                symbols_to_fetch_yf.append(yf_symbol)

        if symbols_to_fetch_yf:
            print(
                f"Fetching {len(symbols_to_fetch_yf)} symbols from yfinance...",
                flush=True,
            )
            try:
                # Use the synchronous batched fetch function with retries
                fetched_info_map = fetch_tickers_info_batched_sync(symbols_to_fetch_yf)

                # Process fetched data and update symbol_prices
                for yf_symbol, info in fetched_info_map.items():
                    # Get current price from fetched info
                    price = safe_get_info(info, "regularMarketPrice")
                    if price == "N/A":  # Fallback
                        price = safe_get_info(info, "previousClose")

                    if isinstance(price, (int, float)):
                        # Map back to original symbol for storage in symbol_prices
                        original_symbol = yf_symbol.replace(
                            "-USD", ""
                        )  # Simple reverse mapping
                        symbol_prices[original_symbol] = float(price)

                        # Cache the newly fetched price
                        cache_key = get_cache_key("alert_price", yf_symbol)
                        # Run async set_cached_data in sync context
                        run_async_in_sync(
                            set_cached_data(
                                cache_key, float(price), CACHE_EXPIRY_SECONDS_SHORT
                            )
                        )
                    else:
                        print(
                            f"Could not get valid price from yfinance info for {yf_symbol}: {price}",
                            flush=True,
                        )

            except Exception as e:
                # Error logged by retry decorator. Failed symbols will not be in symbol_prices.
                print(
                    f"Failed to fetch prices for symbols {symbols_to_fetch_yf} after retries.",
                    flush=True,
                )

        # 4. Iterate through alerts and check against fetched/cached prices
        updated_alerts = []
        for alert in alerts:
            # Use the original alert symbol (without -USD) to look up price
            symbol_to_lookup = alert.symbol.upper()
            target = alert.target_price

            # Get price from the combined map (cached + newly fetched)
            current_price = symbol_prices.get(symbol_to_lookup)

            # print(f"Checking alert for {alert.email} - {symbol_to_lookup}: current={current_price}, target={target}", flush=True) # Debug logging

            if current_price is not None and current_price >= target:
                print(
                    f"ALERT TRIGGERED for {alert.email}: {alert.symbol} is {current_price} (target {target})",
                    flush=True,
                )
                # Send email (requires running async send_email_alert from sync task)
                try:
                    run_async_in_sync(
                        send_email_alert(
                            alert.email,
                            f"{alert.symbol.upper()} Alert!",
                            f"{alert.symbol.upper()} has reached more than ${alert.target_price}. Current price is ${current_price:.2f}!",
                        )
                    )
                    alert.is_active = False  # Deactivate alert after sending
                    updated_alerts.append(alert)  # Collect alerts to update
                except Exception as e:
                    print(
                        f"Failed to send alert email to {alert.email} for {alert.symbol}: {e}",
                        flush=True,
                    )
            # else:
            # print(f"Alert condition not met for {alert.email} - {symbol_to_lookup}", flush=True) # Debug logging if not triggered

        # 5. Commit changes to deactivate triggered alerts
        if updated_alerts:
            print(f"Deactivating {len(updated_alerts)} alerts.", flush=True)
            # SQLAlchemy tracks changes, just need to commit the session
            # db.add(alert) was done in the loop if needed, but with ORM session, modifications are tracked
            db.commit()

    print("Finished checking alerts.", flush=True)


# Note: The original file had commented-out async run_price_check.
# This version keeps the task synchronous as defined in celery_config.py,
# and uses the run_async_in_sync helper to bridge to the async email sender.
# The yfinance fetching is done synchronously using the retry wrapper.
# If you need a fully async Celery worker, you'd need to configure that
# (e.g., using gevent or eventlet workers) and use async yfinance libraries
# or run blocking calls in an executor within the async task.
# This approach balances minimizing yfinance hits with fitting into your current sync worker setup.

# import asyncio
# from fastapi import HTTPException
# from pydantic import EmailStr
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from app.core.db import SessionLocal, SyncSessionLocal
# from app.models.user_alert import UserAlert
# from app.schemas.user_alert import UserAlertCreate
# from app.utils import send_email_alert
# import yfinance as yf
# from celery_config import celery


# # Create Alert
# async def create_user_alert(db: AsyncSession, alert_data: UserAlertCreate,email:EmailStr):
#     existing_alert = await db.execute(
#         select(UserAlert).where(
#             UserAlert.email == email,
#             UserAlert.symbol == alert_data.symbol.upper(),
#             UserAlert.target_price == alert_data.target_price,
#         )
#     )
#     if existing_alert.scalar():
#         raise HTTPException(status_code=400, detail="Alert already exists")

#     alert = UserAlert(
#         email=email,
#         symbol=alert_data.symbol.upper(),
#         target_price=alert_data.target_price,
#     )
#     db.add(alert)
#     await db.commit()
#     await db.refresh(alert)
#     return alert




# # celery = Celery(__name__, broker="redis://redis:6379/0")



# @celery.task
# def run_price_check():
#     print("Starting celery alerts",flush=True)
#     # asyncio.run(
#     # send_email_alert(
#     #    "abdulrehmanb8631@gmail.com",
#     #     "Alert!",
#     #     "btc has reached maximum!",
#     # ))
#     with SyncSessionLocal() as db:
#         alerts = (
#             db.execute(select(UserAlert).where(UserAlert.is_active == True))
#             .scalars()
#             .all()
#         )

#         for alert in alerts:
#             stock_data = yf.Ticker(alert.symbol).info
#             current_price = stock_data.get("regularMarketPrice")

#             print("Checking the price from celery now", flush=True)

#             if current_price and current_price >= alert.target_price:
#                 asyncio.run(
#                     send_email_alert(  # Run async function safely
#                         alert.email,
#                         f"{alert.symbol} Alert!",
#                         f"{alert.symbol} has reached more than ${alert.target_price}. Now its price is at {current_price}!",
#                     )
#                 )
#                 alert.is_active = False
#                 db.commit()

#     print("Finished checking alerts", flush=True)


# # @celery.task
# # async def run_price_check(db: AsyncSession):
# #     alerts = await db.execute(select(UserAlert).where(UserAlert.is_active == True))
# #     alerts = alerts.scalars().all()

# #     for alert in alerts:
# #         stock_data = yf.Ticker(alert.symbol).info
# #         current_price = stock_data.get("currentPrice")

# #         if current_price and current_price >= alert.target_price:
# #             await send_email_alert(
# #                 alert.email,
# #                 f"{alert.symbol} Alert!",
# #                 f"{alert.symbol} has reached ${alert.target_price}!",
# #             )
# #             alert.is_active = False
# #             await db.commit()
