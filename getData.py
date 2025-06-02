import yfinance as yf
import pandas as pd
from datetime import date

tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK-B", "NVDA", "JPM", 
           "V", "UNH", "JNJ", "WMT", "PG", "MA", "HD", "XOM", "BAC", "DIS", "PFE", "KO", 
           "CSCO", "CVX", "ORCL", "NKE", "MRK", "ABT", "TMO", "MCD", "DHR", "CMCSA", 
           "BMY", "LLY", "AVGO", "TXN", "COST", "WFC", "C", "UPS", "RTX", "LIN", "HON", 
           "AMD", "IBM", "QCOM", "INTU", "GE", "CAT", "SBUX"]

# Download daily price data for all tickers
price_data = yf.download(tickers, start="2013-01-01", end="2024-12-31", group_by='ticker')

earnings_all = []

# Get earnings for each stock
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.get_earnings_dates(limit = 40)
        earnings["ticker"] = ticker
        earnings_all.append(earnings)
    except Exception as e:
        print(f"Failed for {ticker}: {e}")

# Create earnings dataset
earnings_df = pd.concat(earnings_all).reset_index()
earnings_df.rename(columns={"index": "Earnings Date"}, inplace=True)
earnings_df["beat"] = (earnings_df["Reported EPS"] > earnings_df["EPS Estimate"]).astype(int)
earnings_df['Earnings Date'] = pd.to_datetime(earnings_df['Earnings Date']).dt.date

# Clean earnings data
earnings_df = earnings_df.dropna(subset=["Reported EPS", "EPS Estimate"])
earnings_df = earnings_df[earnings_df['Earnings Date'] <= date.today()]

earnings_df.to_csv("earnings_data.csv", index = False)