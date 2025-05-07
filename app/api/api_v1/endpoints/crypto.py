from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.crud.crypto import fetch_crypto_data_crud, fetch_historical_data, fetch_historical_data_stock, fetch_historical_data_stock_gbp, fetch_stock_data_crud, fetch_stock_data_crud_gbp, fetch_stock_data_crud_gbp_with_positions, fetch_stock_data_crud_with_positions

from app.utils import crypto_symbols, stock_symbols


router = APIRouter()


@router.get("/usd")
async def get_crypto_data_usd(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    

    data = await fetch_crypto_data_crud(
        db, crypto_symbols[skip : skip + limit], currency="USD"
    )
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/gbp")
async def get_crypto_data_gbp(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    

    data = await fetch_crypto_data_crud(
        db, crypto_symbols[skip : skip + limit], currency="GBP"
    )
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/usd/{symbol}")
async def get_crypto_statistics_usd(symbol: str):
    return fetch_historical_data(symbol, currency="USD")

@router.get("/gbp/{symbol}")
async def get_crypto_statistics_gbp(symbol: str):
    return fetch_historical_data(symbol, currency="GBP")


@router.get("/stocks/usd")
async def get_stock_data_usd(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    

    data = await fetch_stock_data_crud(db, stock_symbols[skip : skip + limit])
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/stocks/usdpositions")
async def get_stock_data_usd_with_positions(
    db: AsyncSession = Depends(get_session)
):

    data = await fetch_stock_data_crud_with_positions(db, stock_symbols)
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/stocks/gbp")
async def get_stock_data_gbp(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, alias="offset"),
    limit: int = Query(10),
):
    

    data = await fetch_stock_data_crud_gbp(
        db, stock_symbols[skip : skip + limit], currency="GBP"
    )
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/stocks/gbppositions")
async def get_stock_data_gbp_with_positions(
    db: AsyncSession = Depends(get_session),
):

    data = await fetch_stock_data_crud_gbp_with_positions(db, stock_symbols, currency="GBP")
    if not data:
        raise HTTPException(status_code=404, detail="No data found")

    return data


@router.get("/stocks/usd/{symbol}")
async def get_stock_statistics_usd(symbol: str):
    return fetch_historical_data_stock(symbol, currency="USD")


@router.get("stocks/gbp/{symbol}")
async def get_stock_statistics_gbp(symbol: str):
    return fetch_historical_data_stock_gbp(symbol)