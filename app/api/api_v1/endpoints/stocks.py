from fastapi import APIRouter, HTTPException
from app.core.config import settings
from typing import List, Dict
import finnhub


finnhub_client = finnhub.Client(api_key=settings.FINNHUB_API_KEY)


router = APIRouter()


@router.get("/symbols", response_model=List[Dict])
async def get_stock_symbols(exchange: str = "US"):
    """
    Fetch a list of stock symbols for a given exchange.
    """
    try:
        symbols = finnhub_client.stock_symbols(exchange)
        return symbols
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/quote")
async def get_stock_quote(symbol: str):
    """
    Get the current quote for a given stock symbol.
    """
    try:
        quote = finnhub_client.quote(symbol)
        if quote:
            return quote
        else:
            raise HTTPException(status_code=404, detail="Symbol not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/candles")
async def get_stock_candles(
    symbol: str,
    resolution: str = "1",
    from_ts: int = 1672531200,
    to_ts: int = 1675219200,
):
    """
    Get historical candles data for a given stock symbol.
    Resolution: 1, 5, 15, 30, 60, D, W, M
    From and To are timestamps in seconds.
    """
    try:
        candles = finnhub_client.stock_candles(symbol, resolution, from_ts, to_ts)
        return candles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
