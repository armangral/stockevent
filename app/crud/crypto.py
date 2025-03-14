import requests
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import yfinance as yf



async def fetch_crypto_data_crud(db: AsyncSession, symbols: List[str], currency: str):
    data = []
    
    
    for symbol in symbols:
        a = symbol["id"]
        url = f"https://api.coingecko.com/api/v3/coins/{a}"
        response = requests.get(url).json()
        print(f"response is {response}")
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
                    "logo_url": response["image"]["large"],  # Fetching logo URL
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


def fetch_historical_data(symbol, currency):
    symbol = symbol["symbol"]
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