import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from catboost import CatBoostClassifier, Pool
import requests
from bs4 import BeautifulSoup
import re

# Choose stock and load model
ticker = "EQT"
category_features = ["sector", "quarter", "day_of_week"]
model = CatBoostClassifier()
model.load_model("catboost_model.cbm")

# Get upcoming earnings date for the stock
stock = yf.Ticker(ticker)
info = stock.info
company_name = info.get("shortName", ticker)
website = info.get("website", None)
description = info.get("longBusinessSummary", "")
prefix = company_name.rstrip(".")
parts = re.split(r'(?<!Inc)(?<!LLC)(?<!Co)(?<!Corp)\. ', description, maxsplit=1)
short_desc = parts[0].strip() + "."
sector = info.get("sector", "N/A")
beta = info.get("beta", np.nan)

print(f"Company Name: {company_name} ({ticker})")
if website:
    print(f"Website: {website}")
    domain = website.replace("https://", "").replace("http://", "").split("/")[0]
    clearbit_logo = f"https://logo.clearbit.com/{domain}?size=512"
    print(f"Logo Link: {clearbit_logo}")
else:
    print("No website on file; can’t build logo URL.")
print(short_desc)
print(f"Sector: {sector}")
print(f"Beta: {beta:.2f}")
today = pd.Timestamp.now().normalize()

try:
    cal = stock.calendar
    if isinstance(cal, pd.DataFrame):
        raw = cal.loc["Earnings Date"][0]
    else:
        raw = cal.get("Earnings Date") or cal.get("earningsDate")
        if isinstance(raw, list):
            raw = raw[0]
        elif isinstance(raw, dict):
            raw = list(raw.values())[0]
    next_earnings_date = pd.to_datetime(raw).tz_localize(None).normalize()
except Exception as e:
    print(f"No upcoming earnings found for {ticker}: {e}")
    exit()

days_until_earnings = (next_earnings_date - today).days
if days_until_earnings > 7:
    wait = days_until_earnings - 7
    next_earnings_date_str = next_earnings_date.strftime("%m-%d-%Y")
    print(f"{ticker}'s next earnings ({next_earnings_date_str}) are in {days_until_earnings} days.")
    check_date_str = (today + timedelta(days = wait)).strftime("%m-%d-%Y")
    print(f"Check back in {wait} day(s), on {check_date_str} for a prediction.")
    exit()


try:
    info = stock.info
    eps_estimate = info.get("forwardEps", None)
    if eps_estimate is None:
        raise KeyError("forwardEps not in info")
    eps_estimate = float(eps_estimate)
except Exception as e:
    print(f"Warning: could not fetch forward EPS estimate ({e}), using fallback.")
    eps_estimate = 0.5

cutoff_date = next_earnings_date - timedelta(days=7)

# Download stock and S&P 500 data
price_data = yf.download(ticker, start="2013-01-01", end = cutoff_date + timedelta(days = 1), auto_adjust = True, progress = False)
spy_data = yf.download("SPY", start="2013-01-01", end = cutoff_date + timedelta(days = 1), auto_adjust = True, progress = False)
price_data = price_data[price_data.index <= cutoff_date]
spy_data = spy_data[spy_data.index <= cutoff_date]
if len(price_data) < 50:
    print(f"Not enough historical data for {ticker} to compute indicators.")
    exit()

# Get features of stock to predict
try:
    close = price_data["Close"].squeeze()
    volume = price_data["Volume"].squeeze()

    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    macd_diff = MACD(close).macd_diff().iloc[-1]
    sma_20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
    sma_50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]
    if sma_50 != 0:
        sma_ratio = sma_20 / sma_50
    else:
        np.nan

    price_return_30d = close.iloc[-1] / close.iloc[-30] - 1
    if len(close) >= 14:
        price_return_7d_before_cutoff = close.iloc[-7] / close.iloc[-14] - 1
    else:
        np.nan

    volatility_30d = close[-30:].pct_change().std()
    volume_avg_30d = volume[-30:].mean()
    volume_max_30d = volume[-30:].max()
    if volume_max_30d != 0:
        volume_avg_30d_normalized = volume_avg_30d / volume_max_30d
    else:
        np.nan

    spy_close = spy_data["Close"].squeeze()
    if len(spy_close) >= 30:
        spy_return = spy_close.iloc[-1] / spy_close.iloc[-30] - 1
    else:
        np.nan

    price_to_avg_30d = close.iloc[-1] / close.iloc[-30:].mean()

    info = stock.info
    sector = info.get("sector", np.nan)
    beta = info.get("beta", np.nan)

    history = stock.get_earnings_dates(limit=40)
    history.index = pd.to_datetime(history.index).tz_localize(None)
    past = history[history.index < next_earnings_date].sort_index(ascending=False).head(4)
    if len(past) >= 1:
        eps_surprises = (past["Reported EPS"] - past["EPS Estimate"]) / past["EPS Estimate"]
        eps_surprise_avg = eps_surprises.mean()
    else:
        eps_surprise_avg = 0.05

    feature_row = {
        "sector": sector,
        "beta": beta,
        "eps_estimate": eps_estimate,
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
        "relative_return_30d": price_return_30d - spy_return,
        "quarter": next_earnings_date.quarter,
        "day_of_week": next_earnings_date.weekday(),
    }
    input_df = pd.DataFrame([feature_row])

    # Predict beat percentage for ticker
    test_pool = Pool(data=input_df, cat_features = category_features)
    probability = model.predict_proba(test_pool)[:, 1][0]
    probability_pct = probability * 100
    date_str = next_earnings_date.strftime("%m-%d-%Y")
    print(f"Earnings Date: {date_str}")
    print(f"Expected EPS: {eps_estimate:.2f}")
    print(f"Probability of Beat: {probability_pct:.2f}%")
    
except Exception as e:
    print(f"Error generating prediction for {ticker}: {e}")
