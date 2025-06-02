import yfinance as yf

tickers = ["AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "BRK.B", "NVDA", "JPM", 
           "V", "UNH", "JNJ", "WMT", "PG", "MA", "HD", "XOM", "BAC", "DIS", "PFE", "KO", 
           "CSCO", "CVX", "ORCL", "NKE", "MRK", "ABT", "TMO", "MCD", "DHR", "CMCSA", 
           "BMY", "LLY", "AVGO", "TXN", "COST", "WFC", "C", "UPS", "RTX", "LIN", "HON", 
           "AMD", "IBM", "QCOM", "INTU", "GE", "CAT", "SBUX"]

# Download daily price data for all tickers
price_data = yf.download(tickers, start="2013-01-01", end="2024-12-31", group_by='ticker')
