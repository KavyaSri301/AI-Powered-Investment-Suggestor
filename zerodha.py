import os
from kiteconnect import KiteConnect
from dotenv import load_dotenv

load_dotenv()  # loads from .env

class ZerodhaClient:
    def __init__(self):
        self.api_key = os.getenv("ZERODHA_API_KEY")
        self.api_secret = os.getenv("ZERODHA_API_SECRET")
        self.access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        self.kite = None
        self.connected = False

        if self.api_key and self.api_secret and self.access_token:
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                self.kite.set_access_token(self.access_token)
                self.connected = True
                print("✅ Connected to Zerodha successfully.")
            except Exception as e:
                print(f"❌ Failed to connect to Zerodha: {e}")
        else:
            print("⚠️ Missing Zerodha credentials in .env file.")

    def get_holdings(self):
        if self.connected:
            try:
                holdings = self.kite.holdings()
                return holdings
            except Exception as e:
                return {"error": f"Failed to fetch holdings: {e}"}
        return {"error": "Not connected"}

    def get_positions(self):
        if self.connected:
            try:
                positions = self.kite.positions()
                return positions
            except Exception as e:
                return {"error": f"Failed to fetch positions: {e}"}
        return {"error": "Not connected"}
