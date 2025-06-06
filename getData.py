import yfinance as yf
import numpy as np
import pandas as pd
from datetime import date, timedelta
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator

tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK-B", "NVDA", "JPM", 
           "V", "UNH", "JNJ", "WMT", "PG", "MA", "HD", "XOM", "BAC", "DIS", "PFE", "KO", 
           "CSCO", "CVX", "ORCL", "NKE", "MRK", "ABT", "TMO", "MCD", "DHR", "CMCSA", 
           "BMY", "LLY", "AVGO", "TXN", "COST", "WFC", "C", "UPS", "RTX", "LIN", "HON", 
           "AMD", "IBM", "QCOM", "INTU", "GE", "CAT", "SBUX"]

# Download price data
end_date = date.today().strftime("%Y-%m-%d")
price_data = yf.download(tickers, start="2013-01-01", end=end_date, group_by='ticker')
spy_data = yf.download("SPY", start="2013-01-01", end=end_date, auto_adjust=True)

# Get earnings data
earnings_all = []
for ticker in tickers:
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.get_earnings_dates(limit=40)
        earnings["ticker"] = ticker
        earnings_all.append(earnings)
    except Exception as e:
        print(f"Failed for {ticker}: {e}")

earnings_df = pd.concat(earnings_all).reset_index()
earnings_df.rename(columns={"index": "Earnings Date"}, inplace=True)
earnings_df["beat"] = (earnings_df["Reported EPS"] > earnings_df["EPS Estimate"]).astype(int)
earnings_df["Earnings Date"] = pd.to_datetime(earnings_df["Earnings Date"]).dt.tz_localize(None)
earnings_df = earnings_df.dropna(subset=["Reported EPS", "EPS Estimate"])
today = pd.Timestamp.now().normalize()
earnings_df = earnings_df[earnings_df["Earnings Date"] <= today]

features = []

for _, row in earnings_df.iterrows():
    ticker = row["ticker"]
    earnings_date = pd.to_datetime(row["Earnings Date"])
    cutoff_date = earnings_date - timedelta(days=7)

    try:
        stock = price_data[ticker]
        stock = stock[stock.index <= cutoff_date]
        if len(stock) < 50:
            continue

        close = stock["Close"]
        volume = stock["Volume"]

        # EPS surprise average (last 4 quarters)
        past_eps = earnings_df[
            (earnings_df["ticker"] == ticker) &
            (earnings_df["Earnings Date"] < earnings_date)
        ].sort_values("Earnings Date", ascending=False).head(4)

        if len(past_eps) == 4:
            eps_surprise_avg = ((past_eps["Reported EPS"] - past_eps["EPS Estimate"]) / past_eps["EPS Estimate"]).mean()
        else:
            eps_surprise_avg = 0.05  # fallback value

        # Technicals
        rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
        macd_diff = MACD(close).macd_diff().iloc[-1]
        sma_20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
        sma_50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]
        if sma_50 != 0:
            sma_ratio = sma_20 / sma_50
        else:
            sma_ratio = np.nan

        if len(close) >= 30:
            price_return_30d = close.iloc[-1] / close.iloc[-30] - 1
        else:
            price_return_30d = np.nan

        if len(close) >= 14:
            price_return_7d_before_cutoff = close.iloc[-7] / close.iloc[-14] - 1
        else:
            price_return_7d_before_cutoff = np.nan
        
        volatility_30d = close[-30:].pct_change().std()
        volume_avg_30d = volume[-30:].mean()
        volume_max_30d = volume[-30:].max()
        if volume_max_30d != 0:
            volume_avg_30d_normalized = volume_avg_30d / volume_max_30d
        else:
            volume_avg_30d_normalized = np.nan

        # SPY return in place of sector return
        spy_cutoff_data = spy_data[spy_data.index <= cutoff_date]
        spy_close = spy_cutoff_data["Close"]
        if len(spy_close) >= 30:
            spy_close_last = spy_close.values[-1]
            spy_close_30 = spy_close.values[-30]
            spy_return = (spy_close_last / spy_close_30 - 1).item()
        else:
            spy_return = np.nan

        price_to_avg_30d = close.iloc[-1] / close[-30:].mean()

        info = yf.Ticker(ticker).info
        beta = info.get("beta", np.nan)

        feature_row = {
            "ticker": ticker,
            "earnings_date": earnings_date.date(),
            'beta': beta,
            "eps_estimate": row["EPS Estimate"],
            "price_to_avg_30d": price_to_avg_30d,
            "eps_surprise_avg": eps_surprise_avg,
            "price_return_30d": price_return_30d,
            "price_return_7d_before_cutoff": price_return_7d_before_cutoff,
            "rsi_14": rsi,
            "macd_diff": macd_diff,
            "sma_ratio_20_50": sma_ratio,
            "volatility_30d": volatility_30d,
            "volume_avg_30d": volume_avg_30d_normalized,
            "spy_return": spy_return,
            "rel_return_30d": price_return_30d - spy_return,
            'quarter': earnings_date.quarter,
            'day_of_week': earnings_date.weekday(),
            "label": row["beat"]
        }

        features.append(feature_row)

    except Exception as e:
        print(f"Error for {ticker} on {earnings_date.date()}: {e}")

features_df = pd.DataFrame(features)
features_df.to_csv("training_dataset.csv", index=False)