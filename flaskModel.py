import re
import os
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
    try:
        # Load model
        model = CatBoostClassifier()
        model.load_model("catboost_model.cbm")

        # Ticker & company info
        ticker = request.args.get("ticker", "NKE").upper()
        stock = yf.Ticker(ticker)
        info = stock.info

        company_name = info.get("shortName", ticker)
        website = info.get("website", None)
        logo = None
        if website:
            domain = website.replace("https://", "").replace("http://", "").split("/")[0]
            logo = f"https://logo.clearbit.com/{domain}?size=512"

        # Short description
        description = info.get("longBusinessSummary", "")
        sentences = re.split(r'(?<!Inc)(?<!LLC)(?<!Co)(?<!Corp)\. ', description)
        short_desc = ". ".join(sentence.strip() for sentence in sentences[:4])
        if not short_desc.endswith("."):
            short_desc += "."

        beta = info.get("beta", np.nan)

        # Next earnings date
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
        earnings_date_str = next_dt.strftime("%Y-%m-%d")

        # EPS estimate
        eps_estimate = info.get("forwardEps", 0.0) or 0.0
        eps_estimate = float(eps_estimate)

        # Historical data cutoff 7 days before earnings
        cutoff_date = next_dt - timedelta(days=7)
        price_data = yf.download(
            ticker,
            start="2013-01-01",
            end=cutoff_date + timedelta(days=1),
            auto_adjust=True,
            progress=False
        )
        spy_data = yf.download(
            "SPY",
            start="2013-01-01",
            end=cutoff_date + timedelta(days=1),
            auto_adjust=True,
            progress=False
        )
        price_data = price_data[price_data.index <= cutoff_date]
        spy_data = spy_data[spy_data.index <= cutoff_date]

        # Compute features
        close = price_data["Close"]
        volume = price_data["Volume"]

        rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
        macd_diff = MACD(close).macd_diff().iloc[-1]
        sma20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
        sma50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]
        sma_ratio = sma20 / sma50 if sma50 != 0 else np.nan

        price_return_30d = close.iloc[-1] / close.iloc[-30] - 1
        price_return_7d_before = (
            close.iloc[-7] / close.iloc[-14] - 1
            if len(close) >= 14 else np.nan
        )

        volatility_30d = close[-30:].pct_change().std()
        volume_avg_30d = volume[-30:].mean()
        volume_max_30d = volume[-30:].max()
        volume_norm = volume_avg_30d / volume_max_30d if volume_max_30d != 0 else np.nan

        spy_close = spy_data["Close"]
        spy_return = (
            spy_close.iloc[-1] / spy_close.iloc[-30] - 1
            if len(spy_close) >= 30 else np.nan
        )

        price_to_avg30d = close.iloc[-1] / close.iloc[-30:].mean()

        # Past earnings surprises
        history = stock.get_earnings_dates(limit=40)
        history.index = pd.to_datetime(history.index).tz_localize(None)
        past = history[history.index < next_dt].sort_index(ascending=False).head(4)
        if len(past) >= 1:
            eps_surprises = (
                past["Reported EPS"] - past["EPS Estimate"]
            ) / past["EPS Estimate"]
            eps_surprise_avg = eps_surprises.mean()
        else:
            eps_surprise_avg = np.nan

        # Assemble feature DataFrame
        feature_row = {
            "sector": info.get("sector", np.nan),
            "beta": beta,
            "eps_estimate": eps_estimate,
            "price_to_avg_30d": price_to_avg30d,
            "eps_surprise_avg": eps_surprise_avg,
            "price_return_30d": price_return_30d,
            "price_return_7d_before_cutoff": price_return_7d_before,
            "rsi_14": rsi,
            "macd_diff": macd_diff,
            "sma_ratio_20_50": sma_ratio,
            "volatility_30d": volatility_30d,
            "volume_avg_30d": volume_norm,
            "spy_return": spy_return,
            "relative_return_30d": price_return_30d - spy_return,
            "quarter": next_dt.quarter,
            "day_of_week": next_dt.weekday(),
        }
        input_df = pd.DataFrame([feature_row])
        test_pool = Pool(data=input_df, cat_features=["sector", "quarter", "day_of_week"])
        prob = model.predict_proba(test_pool)[:, 1][0]
        prob_pct = prob * 100

        # Rescale probability
        def rescale(p, threshold=0.57):
            if p >= threshold:
                return 0.5 + (p - threshold) / (1 - threshold) * 0.5
            else:
                return (p / threshold) * 0.5

        scaled_pct = rescale(prob) * 100

        # Return only requested fields
        result = {
            "company_name": company_name,
            "ticker": ticker,
            "short_description": short_desc,
            "beta": round(beta, 2) if not np.isnan(beta) else None,
            "website": website,
            "logo": logo,
            "earnings_date": earnings_date_str,
            "expected_eps": round(eps_estimate, 2),
            "raw_beat_pct": round(prob_pct, 2),
            "scaled_beat_pct": round(scaled_pct, 2),
        }
        return jsonify(result), 200

    except Exception as e:
        # Return error message as JSON
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)