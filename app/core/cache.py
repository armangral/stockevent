
import redis.asyncio as redis  # Use the async version
import json
import os
import logging  # Import logging
from typing import Any
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Assuming Redis runs on 'redis' host as defined in docker-compose.yaml
# Make sure your .env or config exposes the redis host/port
# Using defaults that match your docker-compose for now
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

# Define cache expiry times in seconds (can make these configurable via settings)
CACHE_EXPIRY_SECONDS_SHORT = (
    60  # For frequently changing data like current price (1 minute)
)
CACHE_EXPIRY_SECONDS_MEDIUM = 300  # For slightly less frequent data (5 minutes)
CACHE_EXPIRY_SECONDS_LONG = (
    3600  # For less volatile data or historical snapshots (1 hour)
)
CACHE_EXPIRY_SECONDS_DAILY = 86400  # For daily summaries (24 hours)


# Create an async Redis client using a connection pool (managed internally by redis-py >= 4.x)
# Use decode_responses=True to automatically decode responses to strings
try:
    redis_client = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
    )
    logger.info(
        f"Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
    # Optional: Ping the server to check connection on startup (can add async ping later if needed)
    # You might add a startup event handler in FastAPI to do an async ping
    # async def startup_event():
    #     try:
    #         await redis_client.ping()
    #         logger.info("Redis connection successful!")
    #     except redis.exceptions.ConnectionError as e:
    #         logger.error(f"Could not connect to Redis: {e}")
    #         # Depending on criticality, you might want to raise an exception or just log and continue
    # app.add_event_handler("startup", startup_event)

except Exception as e:
    logger.error(f"Failed to initialize Redis client: {e}")
    # In a real application, you might want to handle this failure more robustly
    # e.g., raise an error, set a flag to indicate cache is down, etc.
    # For now, we'll let it potentially fail later if Redis is truly unreachable.


def get_cache_key(
    prefix: str,
    symbol: str,
    currency: str | None = None,
    period: str | None = None,
    interval: str | None = None,
) -> str:
    """
    Generates a consistent cache key based on parameters.

    Args:
        prefix: A string indicating the type of data (e.g., "crypto_current", "stock_hist").
        symbol: The ticker symbol (e.g., "BTC", "AAPL").
        currency: Optional currency (e.g., "USD", "GBP").
        period: Optional historical period (e.g., "1d", "1y").
        interval: Optional historical interval (e.g., "15m", "1wk").

    Returns:
        A string representing the cache key.
    """
    # Ensure symbol and currency are uppercase for consistency
    symbol = symbol.upper()
    if currency:
        currency = currency.upper()

    key_parts = [prefix, symbol]
    if currency:
        key_parts.append(currency)
    if period:
        key_parts.append(period)
    if interval:
        key_parts.append(interval)

    # Join parts with a colon for a standard Redis key format
    return ":".join(key_parts)


async def get_cached_data(key: str) -> Any | None:
    """
    Asynchronously retrieves and decodes data from the cache.

    Args:
        key: The cache key.

    Returns:
        The decoded data if found in cache and valid, otherwise None.
    """
    try:
        cached_value = await redis_client.get(key)
        if cached_value:
            try:
                # redis-py[async] with decode_responses=True should return str directly
                # If not using decode_responses=True, you'd need `cached_value.decode('utf-8')`
                return json.loads(cached_value)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in cache for key: {key}. Deleting entry.")
                await redis_client.delete(key)  # Clean up invalid cache entry
                return None
        return None  # Key not found in cache
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error during GET for key {key}: {e}")
        return None  # Treat connection errors as cache misses
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during cache GET for key {key}: {e}"
        )
        return None


async def set_cached_data(key: str, data: Any, expiry_seconds: int):
    """
    Asynchronously encodes and stores data in the cache with an expiration time.

    Args:
        key: The cache key.
        data: The data to cache (should be JSON serializable).
        expiry_seconds: The expiration time in seconds.
    """
    if data is None:
        logger.warning(f"Attempted to cache None data for key: {key}")
        return  # Don't cache None

    try:
        # Encode data to JSON string
        value_to_cache = json.dumps(data)
        # Store in Redis with expiration (ex)
        await redis_client.set(key, value_to_cache, ex=expiry_seconds)
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis connection error during SET for key {key}: {e}")
        # Cache failure is often non-critical, just log and continue
    except TypeError as e:
        logger.error(f"Data for key {key} is not JSON serializable: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during cache SET for key {key}: {e}"
        )


# Optional: Function to close the connection pool on application shutdown
async def close_redis_connection_pool():
    logger.info("Closing Redis connection pool...")
    try:
        await redis_client.close()
        # await redis_client.connection_pool.disconnect() # Depending on redis-py version/usage
        logger.info("Redis connection pool closed.")
    except Exception as e:
        logger.error(f"Error closing Redis connection pool: {e}")

