import yfinance as yf


def get_current_price_stock(symbol: str) -> float:
    """
    Fetches the current price of a given stock symbol using yfinance.

    :param symbol: Stock symbol (e.g., "AAPL", "TSLA").
    :return: Current price as a float.
    """
    try:
        stock = yf.Ticker(f"{symbol}")
        price = stock.history(period="1d")["Close"].iloc[
            -1
        ]  # Get the latest closing price
        return float(price)
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return 0.0  # Default to 0.0 in case of an error
print(get_current_price_stock("AMZN"))