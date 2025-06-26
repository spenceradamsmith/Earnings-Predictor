import os
import re
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from catboost import CatBoostClassifier, Pool
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/predict")
def predict():
    ticker = request.args.get("ticker", "NKE").upper()

    # 1) Load model once per request
    model = CatBoostClassifier()
    model.load_model("catboost_model.cbm")

    # 2) Fetch company & earnings info
    stock = yf.Ticker(ticker)
    info = stock.info

    # Basic fields
    company_name = info.get("shortName", ticker)
    website = info.get("website")
    # logo via Clearbit
    logo = None
    if website:
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        logo = f"https://logo.clearbit.com/{domain}?size=512"

    # Short description
    description = info.get("longBusinessSummary", "")
    sentences = re.split(r'(?<!Inc)(?<!LLC)(?<!Co)(?<!Corp)\. ', description)
    short_desc = ". ".join(sentences[:4]).strip()
    if short_desc and not short_desc.endswith("."):
        short_desc += "."

    beta = info.get("beta", np.nan)

    # 3) Get next earnings date, or return error
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
        next_dt = pd.to_datetime(raw).tz_localize(None).normalize()
    except Exception as e:
        return jsonify({
            "error": f"No upcoming earnings found for {ticker}: {e}"
        }), 200

    # 4) If earnings are more than 7 days out, return your custom message
    days_until = (next_dt - today).days
    if days_until > 7:
        wait = days_until - 7
        next_str  = next_dt.strftime("%m-%d-%Y")
        check_str = (today + timedelta(days=wait)).strftime("%m-%d-%Y")
        return jsonify({
            "error": (
                f"{ticker}'s next earnings ({next_str}) are in {days_until} days. "
                f"Check back in {wait} day(s), on {check_str} for a prediction."
            )
        }), 200

    earnings_date_str = next_dt.strftime("%Y-%m-%d")

    # 5) EPS estimate
    eps_est = float(info.get("forwardEps", 0.0) or 0.0)

    # 6) Download history up to 7 days before earnings
    cutoff = next_dt - timedelta(days=7)
    price_data = yf.download(
        ticker, start="2013-01-01",
        end=cutoff + timedelta(days=1),
        auto_adjust=True, progress=False
    )
    spy_data  = yf.download(
        "SPY", start="2013-01-01",
        end=cutoff + timedelta(days=1),
        auto_adjust=True, progress=False
    )
    price_data = price_data[price_data.index <= cutoff]
    spy_data   = spy_data[spy_data.index   <= cutoff]

    # 7) Compute indicators (force 1-D)
    close  = price_data["Close"]
    volume = price_data["Volume"]
    if getattr(close, "ndim", 1) != 1:
        close = pd.Series(close.values.squeeze(), index=price_data.index)
    if getattr(volume, "ndim", 1) != 1:
        volume = pd.Series(volume.values.squeeze(), index=price_data.index)

    rsi        = RSIIndicator(close, window=14).rsi().iloc[-1]
    macd_diff  = MACD(close).macd_diff().iloc[-1]
    sma20      = SMAIndicator(close, 20).sma_indicator().iloc[-1]
    sma50      = SMAIndicator(close, 50).sma_indicator().iloc[-1]
    sma_ratio  = sma20 / sma50 if sma50 != 0 else np.nan

    price_ret_30d = close.iloc[-1] / close.iloc[-30] - 1
    price_ret_7d  = (
        close.iloc[-7] / close.iloc[-14] - 1
        if len(close) >= 14 else np.nan
    )
    volatility_30d = close[-30:].pct_change().std()
    vol_avg_30d    = volume[-30:].mean()
    vol_max_30d    = volume[-30:].max()
    vol_norm       = vol_avg_30d / vol_max_30d if vol_max_30d != 0 else np.nan

    spy_close  = spy_data["Close"]
    spy_return = (
        spy_close.iloc[-1] / spy_close.iloc[-30] - 1
        if len(spy_close) >= 30 else np.nan
    )
    price_to_avg30d = close.iloc[-1] / close.iloc[-30:].mean()

    # 8) Past surprises
    history = stock.get_earnings_dates(limit=40)
    history.index = pd.to_datetime(history.index).tz_localize(None)
    past = history[history.index < next_dt].sort_index(ascending=False).head(4)
    if len(past) >= 1:
        eps_surprises   = (past["Reported EPS"] - past["EPS Estimate"]) / past["EPS Estimate"]
        eps_surprise_avg = eps_surprises.mean()
    else:
        eps_surprise_avg = np.nan

    # 9) Assemble features and predict
    feature_row = {
        "sector":            info.get("sector", np.nan),
        "beta":              beta,
        "eps_estimate":      eps_est,
        "price_to_avg_30d":  price_to_avg30d,
        "eps_surprise_avg":  eps_surprise_avg,
        "price_return_30d":  price_ret_30d,
        "price_return_7d_before_cutoff": price_ret_7d,
        "rsi_14":            rsi,
        "macd_diff":         macd_diff,
        "sma_ratio_20_50":   sma_ratio,
        "volatility_30d":    volatility_30d,
        "volume_avg_30d":    vol_norm,
        "spy_return":        spy_return,
        "relative_return_30d": price_ret_30d - (spy_return or 0),
        "quarter":           next_dt.quarter,
        "day_of_week":       next_dt.weekday(),
    }
    df       = pd.DataFrame([feature_row])
    pool     = Pool(data=df, cat_features=["sector", "quarter", "day_of_week"])
    prob     = model.predict_proba(pool)[:, 1][0]
    raw_pct  = prob * 100
    def rescale(p, thresh=0.57):
        return (0.5 + (p - thresh)/(1-thresh)*0.5) if p >= thresh else (p/thresh)*0.5
    scaled_pct = rescale(prob) * 100

    # 10) Return only the requested fields
    return jsonify({
        "company_name":     company_name,
        "ticker":           ticker,
        "short_description": short_desc,
        "beta":              None if np.isnan(beta) else round(beta, 2),
        "website":           website,
        "logo":              logo,
        "earnings_date":     earnings_date_str,
        "expected_eps":      round(eps_est, 2),
        "raw_beat_pct":      round(raw_pct, 2),
        "scaled_beat_pct":   round(scaled_pct, 2),
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
