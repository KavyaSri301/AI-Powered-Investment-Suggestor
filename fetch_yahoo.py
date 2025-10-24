
import yfinance as yf
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from nsetools import Nse
from datetime import datetime, timedelta


def fetch_today_90min_data_single_csv(tickers, top_n=20, output_file="intraday_all_tickers.csv"):
    combined_df = pd.DataFrame()
    for ticker in tickers[:top_n]:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="1d", interval="90m")
            if not df.empty:
                df = df.reset_index()
                df["Ticker"] = ticker
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            print(f"Failed {ticker}: {e}")

    if not combined_df.empty:
        cols = ["Ticker"] + [c for c in combined_df.columns if c != "Ticker"]
        combined_df = combined_df[cols]
        combined_df.to_csv(output_file, index=False)
    return combined_df

def fetch_nse_stocks():
    nse = Nse()
    all_stocks = nse.get_stock_codes()  # returns list
    if isinstance(all_stocks, list):
        all_stocks = {s: s for s in all_stocks}
    all_stocks.pop("SYMBOL", None)
    return [symbol + ".NS" for symbol in all_stocks.keys()]

def fetch_yahoo_etfs_mfs():
    """Scrape tickers from Yahoo Finance ETF and Mutual Fund pages."""
    tickers = []
    urls = ["https://finance.yahoo.com/etfs", "https://finance.yahoo.com/mutualfunds"]
    for url in urls:
        r = requests.get(url)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if "/quote/" in a["href"]:
                    symbol = a["href"].split("/quote/")[1].split("?")[0]
                    tickers.append(symbol)
    return tickers
