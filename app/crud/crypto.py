import requests
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import yfinance as yf
from forex_python.converter import CurrencyRates


async def fetch_crypto_data_crud(db: AsyncSession, symbols: List[str], currency: str):
    data = []
    
    
    for symbol in symbols:
        image = symbol["image"]
        symbol = symbol["symbol"]

        try:
            crypto = yf.Ticker(f"{symbol}-{currency}")
            history = crypto.history(period="1d", interval="1h").iloc[-1]
            info = crypto.info

            data.append(
                {
                    "symbol": symbol,
                    "price": round(history["Close"], 2),
                    "market_cap": round(info.get("marketCap", "N/A")),
                    "change_percent": round(
                        info.get("regularMarketChangePercent", 0), 2
                    ),
                    "logo_url": image
                }
            )
        except Exception:
            data.append(
                {
                    "symbol": symbol,
                    "price": "N/A",
                    "market_cap": "N/A",
                    "change_percent": "N/A",
                    "logo_url": "N/A",  # Default in case of failure
                }
            )

    return data


async def fetch_stock_data_crud(db: AsyncSession, tickers: List[str]):
    data = []
    
    for ticker_info in tickers:
        image = ticker_info["logo_url"]
        ticker = ticker_info["symbol"]
        company_name = ticker_info["company_name"]
        
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d").iloc[-1]
            info = stock.info
            
            # Only the specified fields
            data.append({
                "symbol": ticker,
                "price": round(history["Close"], 2),
                "change_percent": round(info.get("regularMarketChangePercent", 0) * 100, 2),
                "market_cap": round(info.get("marketCap", 0)),
                "sector": info.get("sector", "N/A"),
                "industry": company_name,
                "logo_url": image
            })
        except Exception as e:
            data.append({
                "symbol": ticker,
                "price": "N/A",
                "change_percent": "N/A",
                "market_cap": "N/A",
                "sector": "N/A",
                "industry": "N/A",
                "logo_url": "N/A"
            })
            
    return data

async def fetch_stock_data_crud_gbp(db: AsyncSession, tickers: List[str], currency="USD"):
    data = []

    # Fetch USD to GBP conversion using yfinance
    usd_to_gbp_rate = (
        yf.Ticker("GBPUSD=X").history(period="1d")["Close"].iloc[-1]
        if currency == "GBP"
        else 1.0
    )

    for ticker_info in tickers:
        image = ticker_info["logo_url"]
        ticker = ticker_info["symbol"]
        company_name = ticker_info["company_name"]

        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d").iloc[-1]
            info = stock.info

            price = round(history["Close"] * usd_to_gbp_rate, 2)

            data.append(
                {
                    "symbol": ticker,
                    "price": price,
                    "change_percent": round(
                        info.get("regularMarketChangePercent", 0) * 100, 2
                    ),
                    "market_cap": round(info.get("marketCap", 0) * usd_to_gbp_rate),
                    "sector": info.get("sector", "N/A"),
                    "industry": company_name,
                    "logo_url": image,
                }
            )
        except Exception as e:
            data.append(
                {
                    "symbol": ticker,
                    "price": "N/A",
                    "change_percent": "N/A",
                    "market_cap": "N/A",
                    "sector": "N/A",
                    "industry": "N/A",
                    "logo_url": "N/A",
                }
            )

    return data


def fetch_historical_data(symbol, currency):
    # symbol = symbol["symbol"]
    try:
        crypto = yf.Ticker(f"{symbol}-{currency}")
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
            history = crypto.history(period=period, interval=interval)
            entries = []
            step = max(len(history) // 70, 1)
            for i in range(0, len(history), step):
                current_price = history.iloc[i]["Close"]
                prev_price = history.iloc[i - 1]["Close"] if i > 0 else current_price
                change = round(current_price - prev_price, 2)
                percent_change = (
                    round((change / prev_price) * 100, 2) if prev_price != 0 else 0
                )
                entries.append(
                    {
                        "Time": history.index[i],
                        "Price": round(current_price, 2),
                        "Change": change,
                        "% Change": percent_change,
                    }
                )
            data[label] = entries
        return data
    except Exception:
        return {"error": "Data fetch failed"}