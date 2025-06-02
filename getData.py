import yfinance as yf
import pandas as pd

tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK-B", "NVDA", "JPM", 
           "V", "UNH", "JNJ", "WMT", "PG", "MA", "HD", "XOM", "BAC", "DIS", "PFE", "KO", 
           "CSCO", "CVX", "ORCL", "NKE", "MRK", "ABT", "TMO", "MCD", "DHR", "CMCSA", 
           "BMY", "LLY", "AVGO", "TXN", "COST", "WFC", "C", "UPS", "RTX", "LIN", "HON", 
           "AMD", "IBM", "QCOM", "INTU", "GE", "CAT", "SBUX"]

# Download daily price data for all tickers
price_data = yf.download(tickers, start="2013-01-01", end="2024-12-31", group_by='ticker')

earnings_all = []

for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.get_earnings_dates(limit = 40)
        earnings["ticker"] = ticker
        earnings_all.append(earnings)
    except Exception as e:
        print(f"Failed for {ticker}: {e}")

earnings_df = pd.concat(earnings_all)
earnings_df["beat"] = (earnings_df["Reported EPS"] > earnings_df["EPS Estimate"]).astype(int)
earnings_df.to_csv("earnings_data.csv")