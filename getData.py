import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from datetime import date

tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK-B", "NVDA", "JPM", 
           "V", "UNH", "JNJ", "WMT", "PG", "MA", "HD", "XOM", "BAC", "DIS", "PFE", "KO", 
           "CSCO", "CVX", "ORCL", "NKE", "MRK", "ABT", "TMO", "MCD", "DHR", "CMCSA", 
           "BMY", "LLY", "AVGO", "TXN", "COST", "WFC", "C", "UPS", "RTX", "LIN", "HON", 
           "AMD", "IBM", "QCOM", "INTU", "GE", "CAT", "SBUX"]

# Download daily price data for all tickers
end_date = date.today().strftime("%Y-%m-%d")
price_data = yf.download(tickers, start = "2013-01-01", end = end_date, group_by = 'ticker')
spy_data = yf.download("SPY", start = "2013-01-01", end = end_date, auto_adjust = True)

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

features = []

for i, row in earnings_df.iterrows():
    ticker = row["ticker"]
    earnings_date = pd.to_datetime(row["Earnings Date"])

    try:
        # Get stock price data before earnings
        stock = price_data[ticker]
        stock = stock[stock.index < earnings_date]
        stock = stock.tail(14)

        if len(stock) < 10:
            continue

        close_price = stock["Close"]
        open_price = stock["Open"]
        volume = stock["Volume"]
        high = stock["High"]
        low = stock["Low"]
        returns = close_price.pct_change().dropna()

        # SPY last 10 days before earnings
        spy_tenDays = spy_data[(spy_data.index < earnings_date)].tail(10)
        spy_returns = spy_tenDays["Close"].pct_change().dropna()

        # Linear regression slope helper
        def get_slope(series):
            X = np.arange(len(series)).reshape(-1, 1)
            y = series.values.reshape(-1, 1)
            return LinearRegression().fit(X, y).coef_[0][0]
        
        # Feature dictionary for each row
        feature_row = {
            "ticker": ticker,
            "earnings_date": earnings_date.date(),
            "3_day_return": close_price[-3:].pct_change().sum(),
            "5_day_return": close_price[-5:].pct_change().sum(),
            "10_day_return": close_price.pct_change().sum(),
            "day_before_return": close_price.iloc[-1] / close_price.iloc[-2] - 1,
            "momentum": close_price.iloc[-1] / close_price.mean(),
            "price_slope": get_slope(close_price),
            "close_above_ma": int(close_price.iloc[-1] > close_price.mean()),
            "10_day_volatility": returns.std(),
            "intraday_volatility": ((high - low) / open_price).mean(),
            "volume_ratio": volume.iloc[-1] / volume.mean(),
            "volume_slope": get_slope(volume),
            "volume_above_avg": int(volume.iloc[-1] > volume.mean()),
            "is_q4": int(earnings_date.month in [10, 11, 12]),
            "month": earnings_date.month,
            "day_of_week": earnings_date.weekday(),
            "SP500_5_day_return": spy_tenDays["Close"].pct_change().tail(5).sum().item(),
            "SP500_volatility_10d": spy_returns.std().item(),
            "beat": row["beat"]
        }
        features.append(feature_row)
    
    except Exception as e:
        print(f"Error for {ticker} on {earnings_date.date()}: {e}")

features_df = pd.DataFrame(features)
features_df.to_csv("training_dataset.csv", index = False)